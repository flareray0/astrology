import argparse
import json
import logging
import os
import swisseph as swe
from datetime import datetime
from itertools import combinations
from pathlib import Path

from aspect_engine import interpret_aspect
from phase_engine import (
    phase_alignment_score,
    phase_difference_deg,
    phase_resonance_pair,
    phase_resonance_triple,
)

logger = logging.getLogger(__name__)

# =======================
# 0. 入力設定ブロック（差分追加）
# USE_CONFIG_BLOCK = True  → ここで日時・座標を一括設定
# USE_CONFIG_BLOCK = False → 3.使用例セクション内で個別設定（従来動作）
# =======================

USE_CONFIG_BLOCK = True

# --- ネイタル ---
NATAL_DATE  = (1984, 11, 15)   # (年, 月, 日)
NATAL_TIME  = "11:27"          # ローカル時刻 HH:MM
NATAL_TZ    = 9                # UTC+? (日本なら9)
NATAL_LAT   = 37.38
NATAL_LON   = 140.18

# --- プログレス ---
PROGRESS_DATE = (1984, 12, 26)
PROGRESS_TIME = "00:00"
PROGRESS_TZ   = 9
PROGRESS_LAT  = 37.38
PROGRESS_LON  = 140.18

# --- トランジット ---
TRANSIT_DATE = (2026, 2, 12)
TRANSIT_TIME = "00:00"
TRANSIT_TZ   = 9
TRANSIT_LAT  = 37.38
TRANSIT_LON  = 140.18

# --- シナストリー相手（synastryモード時のみ使用） ---
PERSON2_DATE = (1967, 5, 13)
PERSON2_TIME = "00:00"
PERSON2_TZ   = 9
PERSON2_LAT  = 35.68
PERSON2_LON  = 139.65

# --- レポート対象者名 ---
PERSON_NAME = "あなた"

# =======================
# 1. 設定セクション
# =======================

# アスペクトごとの許容オーブ（日本語表記）
MAJOR_ASPECTS = {
    'コンジャンクション': (0, 10),
    'オポジション': (180, 8),
    'トライン': (120, 6),
    'スクエア': (90, 6),
    'セクスタイル': (60, 4),
}

MINOR_ASPECTS = {
    'クインカンクス（150°）': (150, 3),
    'セミスクエア（45°）': (45, 2),
    'セスキコードレート（135°）': (135, 2),
    'セミセクスタイル（30°）': (30, 2),
    'クインタイル（72°）': (72, 1),
    'バイクインタイル（144°）': (144, 1),
    'ノヴァイル（40°）': (40, 1),
    'ビノヴァイル（80°）': (80, 1),
    'クァドノヴァイル（160°）': (160, 1),
    'セプタイル（51.43°）': (51.43, 1),
    'バイセプタイル（102.86°）': (102.86, 1),
    'トライセプタイル（154.29°）': (154.29, 1),
}

# 複合アスペクトごとの許容オーブ（日本語表記）
COMPOSITE_ASPECTS = {
    'ヨッド': {'type': 'yod', 'orbs': 3},
    'グランドクロス': {'type': 'grand_cross', 'orbs': 5},
    'Tスクエア': {'type': 't_square', 'orbs': 5},
    'グランドトライン': {'type': 'grand_trine', 'orbs': 5},
    'キート': {'type': 'kite', 'orbs': 5},
    'ミスティックレクタングル': {'type': 'mystic_rectangle', 'orbs': 5},
    'レクタングル': {'type': 'rectangle', 'orbs': 5},
    'スター': {'type': 'star', 'orbs': 5},
    'ヴェース': {'type': 'vase', 'orbs': 5},
    # 必要に応じて他の複合アスペクトも追加
}

# 星座のリスト（日本語表記）
SIGNS = [
    "牡羊座", "牡牛座", "双子座", "蟹座", "獅子座", "乙女座",
    "天秤座", "蠍座", "射手座", "山羊座", "水瓶座", "魚座"
]

# 惑星と小惑星のリスト（日本語表記）
PLANETS = {
    swe.SUN: "太陽",
    swe.MOON: "月",
    swe.MERCURY: "水星",
    swe.VENUS: "金星",
    swe.MARS: "火星",
    swe.JUPITER: "木星",
    swe.SATURN: "土星",
    swe.URANUS: "天王星",
    swe.NEPTUNE: "海王星",
    swe.PLUTO: "冥王星",
    swe.MEAN_NODE: "ドラゴンヘッド",  # Mean Node
    swe.TRUE_NODE: "トゥルーノード",  # True Node
    swe.MEAN_APOG: "リリス",
    swe.OSCU_APOG: "トゥルーリリス",
    swe.CHIRON: "キロン",
    swe.PHOLUS: "フォルス",
    swe.CERES: "セレス",
    swe.PALLAS: "パラス",
    swe.JUNO: "ジュノー",
    swe.VESTA: "ベスタ",
}

# 小惑星の追加
ASTEROIDS = {
    swe.AST_OFFSET + 433: "エロス",
    swe.AST_OFFSET + 399: "ペルセポネ",
}

# フラグの設定
include_asteroids = True          # 小惑星を含める場合はTrueに
include_minor_aspects = True     # マイナーアスペクトを含める場合はTrueに
include_composite_aspects = True # 複合アスペクトを含める場合はTrueに

# 使用するハウスシステムの指定（例：コッホハウス）
hsys = 'K'

# チャート種別の指定
CHART_TYPE_LABELS = {
    "natal": "ネイタルチャート（出生図）",
    "progressed": "プログレス（二次進行）",
    "transit": "トランジット（現在の運行）",
    "triple": "トリプルチャート（ネイタル＋プログレス＋トランジット）",
    "synastry": "シナストリー（相性）",
}

STRUCTURED_SUMMARY_LABELS = {
    "natal": "出生傾向の要点サマリー",
    "progressed": "内面変化の要点サマリー",
    "transit": "時期運の要点サマリー",
    "triple": "三層統合の要点サマリー",
    "synastry": "相性の要点サマリー",
}

STRUCTURED_SUMMARY_GUIDANCE = {
    "natal": "生まれ持った傾向と、活かしやすい動き方を短時間で確認するための整理版です。",
    "progressed": "最近の内面変化と、今の自分に合う進め方を素早くつかむための整理版です。",
    "transit": "いま反応しやすい外部テーマと、時期の使い方を先に把握するための整理版です。",
    "triple": "本質・内面変化・外部時期を一枚で見比べ、優先順位を決めやすくする整理版です。",
    "synastry": "相手との噛み合いやすい点と、調整が要る点を短時間で確認するための整理版です。",
}

LLM_READING_INTENTS = {
    "natal": "出生図の核となる資質と、日常で活かしやすい動きを読み解く",
    "progressed": "最近の内面変化と、今の自分に合う運用への更新点を読み解く",
    "transit": "いま強く反応しやすい外部テーマと、時期の使い方を読み解く",
    "triple": "本質・内面変化・外部時期の重なりから、優先順位を読み解く",
    "synastry": "二人の噛み合いやすい点と調整ポイントを、関係運用の視点で読み解く",
}

LEGACY_MODE_ALIASES = {
    "triple_chart": "triple",
}

chart_mode = "triple"

USE_USCS_PHASE = os.getenv("USE_USCS_PHASE", "1").lower() in {"1", "true", "yes", "on"}
USCS_VERBOSE = os.getenv("USCS_VERBOSE", "0").lower() in {"1", "true", "yes", "on"}


EPHEMERIS_ENV_VAR = "ASTROLOGY_EPHE_PATH"
def is_valid_ephemeris_dir(path: Path) -> bool:
    """Swiss Ephemeris ファイル群が配置されているディレクトリかを判定する。"""
    if not path or not path.is_dir():
        return False

    normalized_names = {p.name.lower() for p in path.iterdir() if p.is_file()}
    if "sefstars.txt" in normalized_names:
        return True

    se1_files = [name for name in normalized_names if name.startswith("se") and name.endswith(".se1")]
    return len(se1_files) >= 1


def _discover_dynamic_ephemeris_candidates(base_dir: Path) -> list[Path]:
    """`ephe` を含む名前のディレクトリを 1 階層だけ探索して候補に追加する。"""
    if not base_dir.exists() or not base_dir.is_dir():
        return []

    dynamic_candidates: list[Path] = []
    for child in base_dir.iterdir():
        if child.is_dir() and "ephe" in child.name.lower():
            dynamic_candidates.append(child)
    return dynamic_candidates


def _build_ephemeris_candidates() -> list[Path]:
    module_dir = Path(__file__).resolve().parent
    cwd = Path.cwd()

    candidates = [
        module_dir / "data" / "ephemeris",
        module_dir / "ephemeris",
        module_dir / "data" / "ephe",
        module_dir / "ephe",
    ]

    if cwd != module_dir:
        candidates.extend([
            cwd / "data" / "ephemeris",
            cwd / "ephemeris",
            cwd / "data" / "ephe",
            cwd / "ephe",
        ])

    candidates.extend(_discover_dynamic_ephemeris_candidates(module_dir))
    if cwd != module_dir:
        candidates.extend(_discover_dynamic_ephemeris_candidates(cwd))

    unique_candidates: list[Path] = []
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved not in unique_candidates:
            unique_candidates.append(resolved)
    return unique_candidates


def resolve_ephemeris_path(ephe_path: str | None = None) -> tuple[str, str, list[str]]:
    """環境変数優先 + 指定順のリポジトリ相対候補から ephemeris パスを解決する。"""
    searched: list[str] = []

    if ephe_path:
        candidate = Path(ephe_path).expanduser().resolve()
        searched.append(str(candidate))
        if is_valid_ephemeris_dir(candidate):
            return str(candidate), "explicit argument", searched
        raise FileNotFoundError(
            f"[EPHE] 指定された path は Swiss Ephemeris ディレクトリとして無効です: {candidate}"
        )

    env_path = os.getenv(EPHEMERIS_ENV_VAR)
    if env_path:
        env_candidate = Path(env_path).expanduser().resolve()
        searched.append(str(env_candidate))
        if is_valid_ephemeris_dir(env_candidate):
            return str(env_candidate), f"{EPHEMERIS_ENV_VAR}", searched

    for candidate in _build_ephemeris_candidates():
        searched.append(str(candidate))
        if is_valid_ephemeris_dir(candidate):
            return str(candidate), "repo candidate", searched

    searched_lines = "\n - " + "\n - ".join(searched)
    raise FileNotFoundError(
        "[EPHE] Swiss Ephemeris ファイルが見つかりません。"
        f"\n探索順: {EPHEMERIS_ENV_VAR} -> data/ephemeris -> ephemeris -> data/ephe -> ephe"
        f"\n環境変数 {EPHEMERIS_ENV_VAR} で明示指定するか、次の候補に配置してください:{searched_lines}"
    )


def configure_ephemeris(ephe_path: str | None = None) -> str:
    """Swiss Ephemeris の参照先を設定し、実際に使うパスを返す。"""
    resolved, resolved_from, _ = resolve_ephemeris_path(ephe_path)
    os.environ[EPHEMERIS_ENV_VAR] = resolved
    swe.set_ephe_path(Path(resolved).as_posix())
    logger.info("[EPHE] using: %s", resolved)
    logger.info("[EPHE] resolved from: %s", resolved_from)
    return resolved


def configure_ephemeris_path(ephe_path: str | None = None) -> str:
    """後方互換ラッパー。旧コードの固定パス失敗時は自動探索へフォールバック。"""
    if ephe_path:
        try:
            return configure_ephemeris(ephe_path)
        except FileNotFoundError:
            logger.warning("[EPHE] fallback to auto-discovery because invalid explicit path: %s", ephe_path)
    return configure_ephemeris(None)


def debug_ephemeris_path() -> dict:
    """解決結果と探索候補を返すデバッグ用ヘルパー。"""
    resolved, resolved_from, searched = resolve_ephemeris_path()
    return {
        "resolved_path": resolved,
        "resolved_from": resolved_from,
        "searched_candidates": searched,
        "is_valid": is_valid_ephemeris_dir(Path(resolved)),
    }


def print_ephemeris_status() -> dict:
    """現在の ephemeris 解決状態を標準出力へ表示する。"""
    status = debug_ephemeris_path()
    print(f"[EPHE] using: {status['resolved_path']}")
    print(f"[EPHE] resolved from: {status['resolved_from']}")
    print(f"[EPHE] valid directory: {status['is_valid']}")
    return status


EPHEMERIS_PATH = configure_ephemeris()

# 複合アスペクト検出から除外する天体・感受点（標準的占星術慣習に基づく）
# ASC/DSC/MC/IC は出生時刻誤差の影響が大きいため除外
# テール類はヘッドと180°固定のため重複検出を防ぐために除外
COMPOSITE_SKIP = {
    'アセンダント',
    'ディセンダント',
    'MC（ミッドヘヴン）',
    'IC（天底）',
    'バーテクス',
    'パート・オブ・フォーチュン',
    'ドラゴンテール',
    'トゥルーテール',
}

# ノード軸の表示・正規化設定
# - "true": トゥルーノード系を代表採用（デフォルト）
# - "mean": Meanノード系を代表採用
# - "merged": 「ノード軸（ヘッド/テール）」として統合
NODE_MODE = "true"

# ノード軸の定義的アスペクト（常に出やすい組み合わせ）を表示するか
SHOW_STRUCTURAL_NODE_ASPECTS = False

NODE_NORMALIZE_RULES = {
    "ドラゴンヘッド": {"alias_group": "node_head", "mode": "mean", "merged": "ノード軸ヘッド"},
    "トゥルーノード": {"alias_group": "node_head", "mode": "true", "merged": "ノード軸ヘッド"},
    "ドラゴンテール": {"alias_group": "node_tail", "mode": "mean", "merged": "ノード軸テール"},
    "トゥルーテール": {"alias_group": "node_tail", "mode": "true", "merged": "ノード軸テール"},
}

STRUCTURAL_ASPECT_KEYS = {
    ("node_head", "オポジション", "node_tail"),
    ("node_head", "コンジャンクション", "node_head"),
    ("node_tail", "コンジャンクション", "node_tail"),
}

# =======================
# 2. 関数定義セクション
# =======================

def convert_time_to_ut_decimal_hours(time_str, timezone_offset_hours):
    """
    ローカル時刻（HH:MM形式）と時差を用いて、UTC時間を小数時間で返します。
    """
    time_format = "%H:%M"
    try:
        time_obj = datetime.strptime(time_str, time_format)
    except ValueError as error:
        raise ValueError(
            f"time_str は HH:MM（24時間表記）で指定してください。入力値: {time_str}"
        ) from error
    local_hour = time_obj.hour
    local_minute = time_obj.minute

    total_local_minutes = local_hour * 60 + local_minute
    total_ut_minutes = total_local_minutes - timezone_offset_hours * 60
    total_ut_minutes = total_ut_minutes % 1440
    ut_decimal_hours = total_ut_minutes / 60.0

    return ut_decimal_hours

def get_house(lon, cusps):
    """
    指定された経度がどのハウスに属するかを判定します。
    """
    epsilon = 1e-9
    lon = lon % 360.0
    for i in range(1, 13):
        cusp_start = cusps[i] % 360.0
        cusp_end = cusps[i + 1] % 360.0 if i < 12 else cusps[1] % 360.0
        if cusp_start <= cusp_end:
            if cusp_start - epsilon <= lon < cusp_end:
                return i
        else:
            # 360度をまたぐ場合
            if lon >= cusp_start - epsilon or lon < cusp_end:
                return i
    return 12

def calculate_astrology_data(julian_day, lat, lon, hsys='P', include_asteroids=True):
    """
    指定された日時、緯度、経度に基づいて天体の位置を計算します。
    逆行情報も含めます。
    """
    configure_ephemeris(os.getenv(EPHEMERIS_ENV_VAR) or None)

    # 使用する惑星リストを作成
    planets = list(PLANETS.keys())
    if include_asteroids:
        planets += list(ASTEROIDS.keys())

    iflag = swe.FLG_SWIEPH | swe.FLG_SPEED

    # ハウスの計算
    try:
        hsys_bytes = hsys.encode('utf-8')
        cusps, ascmc = swe.houses_ex(julian_day, lat, lon, hsys_bytes)
        # インデックスを1から始めたいので先頭にダミーを追加
        cusps = [0.0] + list(cusps)
    except Exception as e:
        logger.error("ハウス計算中にエラーが発生しました: %s", e)
        return [], []

    ascendant = ascmc[0]
    mc = ascmc[1]
    vertex = ascmc[3]
    descendant = (ascendant + 180.0) % 360.0
    ic = (mc + 180.0) % 360.0

    astrology_data = []

    sun_lon = None
    sun_house = None
    moon_lon = None

    # 惑星や小惑星の位置を取得
    for planet in planets:
        try:
            planet_name = PLANETS.get(planet, ASTEROIDS.get(planet, f"不明惑星 ({planet})"))
            planet_info = swe.calc_ut(julian_day, planet, iflag)
            positions = planet_info[0]
            if len(positions) < 6:
                raise ValueError(f"Unexpected planet_info format for {planet_name}: {planet_info}")
            lon_deg = positions[0] % 360.0
            speed = positions[3]  # 経度方向の速度
            sign = int(lon_deg // 30) % 12
            house = get_house(lon_deg, cusps)
            retrograde = speed < 0  # 逆行フラグ

            # 太陽と月の位置を保存（パート・オブ・フォーチュン計算用）
            if planet == swe.SUN:
                sun_lon = lon_deg
                sun_house = house
            elif planet == swe.MOON:
                moon_lon = lon_deg

            # ここでドラゴンヘッド・トゥルーノードそれぞれのテールを追加
            if planet == swe.MEAN_NODE:
                # ドラゴンテール（Mean Node の180°先）
                tail_lon = (lon_deg + 180.0) % 360.0
                tail_sign = int(tail_lon // 30) % 12
                tail_house = get_house(tail_lon, cusps)
                astrology_data.append({
                    'planet': 'ドラゴンテール',
                    'sign': SIGNS[tail_sign],
                    'longitude': tail_lon,
                    'house': tail_house,
                    'retrograde': retrograde  # 同じ逆行フラグを付与
                })
            elif planet == swe.TRUE_NODE:
                # トゥルーテール（True Node の180°先）
                tail_lon = (lon_deg + 180.0) % 360.0
                tail_sign = int(tail_lon // 30) % 12
                tail_house = get_house(tail_lon, cusps)
                astrology_data.append({
                    'planet': 'トゥルーテール',
                    'sign': SIGNS[tail_sign],
                    'longitude': tail_lon,
                    'house': tail_house,
                    'retrograde': retrograde
                })

            # 通常の天体データを astrology_data に追加
            astrology_data.append({
                'planet': planet_name,
                'sign': SIGNS[sign],
                'longitude': lon_deg,
                'house': house,
                'retrograde': retrograde
            })
        except Exception as e:
            logger.warning("惑星 %s の処理中にエラーが発生しました: %s", planet_name, e)
            continue

    # バーテクスを追加
    try:
        vertex_lon = vertex % 360.0
        vertex_sign = int(vertex_lon // 30) % 12
        vertex_house = get_house(vertex_lon, cusps)
        astrology_data.append({
            'planet': 'バーテクス',
            'sign': SIGNS[vertex_sign],
            'longitude': vertex_lon,
            'house': vertex_house,
            'retrograde': False
        })
    except Exception as e:
        logger.warning("バーテクスの計算中にエラーが発生しました: %s", e)

    # パート・オブ・フォーチュン
    if sun_lon is not None and moon_lon is not None and ascendant is not None:
        if sun_house is not None:
            # 太陽が7～12ハウスなら昼間
            if 7 <= sun_house <= 12:
                pof_lon = (ascendant + moon_lon - sun_lon) % 360.0
            else:
                pof_lon = (ascendant + sun_lon - moon_lon) % 360.0
            sign = int(pof_lon // 30) % 12
            house = get_house(pof_lon, cusps)
            astrology_data.append({
                'planet': 'パート・オブ・フォーチュン',
                'sign': SIGNS[sign],
                'longitude': pof_lon,
                'house': house,
                'retrograde': False
            })

    # 特別なポイント（ASC, MCなど）
    special_points = [
        ('アセンダント', ascendant, 1),
        ('ディセンダント', descendant, 7),
        ('MC（ミッドヘヴン）', mc, 10),
        ('IC（天底）', ic, 4),
    ]
    for name, point_lon, default_house in special_points:
        try:
            point_lon = point_lon % 360.0
            sign = int(point_lon // 30) % 12
            if default_house is not None:
                house = default_house
            else:
                house = get_house(point_lon, cusps)
            astrology_data.append({
                'planet': name,
                'sign': SIGNS[sign],
                'longitude': point_lon,
                'house': house,
                'retrograde': False
            })
        except Exception as e:
            logger.warning("特別なポイント %s の処理中にエラーが発生しました: %s", name, e)
            continue

    return astrology_data, cusps



def classify_uscs_phase_label(phase_delta_deg: float, resonance_score: float) -> str:
    """位相差と共鳴強度から補助ラベルを返す。"""
    if phase_delta_deg <= 12 and resonance_score >= 0.9:
        return "強い同相"
    if resonance_score >= 0.78:
        return "調和共鳴"
    if phase_delta_deg >= 168 and resonance_score <= 0.2:
        return "逆相対立"
    if 78 <= phase_delta_deg <= 102:
        return "緊張干渉"
    if 138 <= phase_delta_deg <= 162:
        return "変換点"
    return "中間共鳴"


def build_phase_metrics(a_deg: float, b_deg: float) -> dict:
    delta = phase_difference_deg(a_deg, b_deg)
    alignment = phase_alignment_score(a_deg, b_deg)
    resonance = phase_resonance_pair(a_deg, b_deg)
    return {
        "phase_delta_deg": round(delta, 3),
        "phase_alignment_score": round(alignment, 3),
        "phase_resonance_score": round(resonance, 3),
        "uscs_label": classify_uscs_phase_label(delta, resonance),
    }


def calculate_synastry_phase_metrics(person1_chart: list[dict], person2_chart: list[dict]) -> dict:
    priority_pairs = [
        ("太陽", "月"),
        ("金星", "火星"),
        ("月", "土星"),
        ("金星", "土星"),
        ("水星", "水星"),
        ("月", "月"),
        ("太陽", "金星"),
    ]
    p1_map = {p.get("planet"): p for p in person1_chart}
    p2_map = {p.get("planet"): p for p in person2_chart}
    pairs = []
    for left, right in priority_pairs:
        if left not in p1_map or right not in p2_map:
            continue
        metrics = build_phase_metrics(float(p1_map[left]["longitude"]), float(p2_map[right]["longitude"]))
        pairs.append({"pair": f"{left}-{right}", **metrics})

    if not pairs:
        return {
            "relationship_phase_score": 0.0,
            "strongest_phase_pairs": [],
            "emotional_phase_coupling": 0.0,
            "attraction_phase_coupling": 0.0,
            "phase_narrative": "位相情報が不足しているため、通常の相性解釈を優先しました。",
        }

    relationship_score = sum(x["phase_resonance_score"] for x in pairs) / len(pairs)
    strongest = sorted(pairs, key=lambda x: x["phase_resonance_score"], reverse=True)[:3]

    emotional_candidates = [x for x in pairs if x["pair"] in {"太陽-月", "月-月", "月-土星"}]
    attraction_candidates = [x for x in pairs if x["pair"] in {"金星-火星", "太陽-金星", "金星-土星"}]
    emotional = sum(x["phase_resonance_score"] for x in emotional_candidates) / len(emotional_candidates) if emotional_candidates else relationship_score
    attraction = sum(x["phase_resonance_score"] for x in attraction_candidates) / len(attraction_candidates) if attraction_candidates else relationship_score

    if relationship_score >= 0.78:
        narrative = "全体として波長が合いやすく、二人のやり取りが自然に噛み合いやすい関係です。"
    elif relationship_score >= 0.58:
        narrative = "引き合いと違和感が交互に働き、意識し合うほど関係が深まりやすい組み合わせです。"
    else:
        narrative = "緊張を通じて相手を強く意識しやすく、忘れにくい関係として残りやすいでしょう。"

    return {
        "relationship_phase_score": round(relationship_score, 3),
        "strongest_phase_pairs": strongest,
        "emotional_phase_coupling": round(emotional, 3),
        "attraction_phase_coupling": round(attraction, 3),
        "phase_narrative": narrative,
    }


def calculate_triple_phase_metrics(natal_chart: list[dict], progressed_chart: list[dict], transit_chart: list[dict]) -> dict:
    n_map = {p.get("planet"): p for p in natal_chart}
    p_map = {p.get("planet"): p for p in progressed_chart}
    t_map = {p.get("planet"): p for p in transit_chart}
    common = [name for name in n_map.keys() if name in p_map and name in t_map]
    triples = []
    for name in common:
        r = phase_resonance_triple(
            float(n_map[name]["longitude"]),
            float(p_map[name]["longitude"]),
            float(t_map[name]["longitude"]),
        )
        triples.append({"planet": name, "triple_phase_resonance": round(r, 3)})

    if not triples:
        return {
            "triple_phase_resonance": 0.0,
            "triple_phase_tension": 0.0,
            "triple_phase_focus": 0.0,
            "focus_planets": [],
            "phase_narrative": "三層比較に必要な共通天体が不足しています。",
        }

    avg = sum(x["triple_phase_resonance"] for x in triples) / len(triples)
    top = sorted(triples, key=lambda x: x["triple_phase_resonance"], reverse=True)[:3]
    tension = max(0.0, 1.0 - avg)
    focus = (sum(x["triple_phase_resonance"] for x in top) / max(1, len(top)))

    if avg >= 0.72:
        narrative = "生まれ持った核・最近の内面変化・今の外部刺激が同じテーマへ収束しやすい時期です。"
    elif avg >= 0.5:
        narrative = "三層が部分的に重なり、テーマを選んで集中するほど流れを活かしやすい局面です。"
    else:
        narrative = "三層のズレがあるため、緊張が強い分だけ課題を意識しやすいタイミングです。"

    return {
        "triple_phase_resonance": round(avg, 3),
        "triple_phase_tension": round(tension, 3),
        "triple_phase_focus": round(focus, 3),
        "focus_planets": top,
        "phase_narrative": narrative,
    }
def calculate_aspects(
    astro_data1,
    astro_data2,
    include_minor_aspects=True,
    deduplicate_when_same_chart=True,
):
    """
    二つの天体データセット間のアスペクトを計算します。
    """
    aspects = []
    same_chart_comparison = deduplicate_when_same_chart and astro_data1 is astro_data2
    # 注意: is はオブジェクト同一性で判定するため、list() 等でコピーして渡すと
    #       同一チャートでも False になり重複が生じる。呼び出し側で同じ変数を渡すこと。

    if same_chart_comparison:
        pair_iter = combinations(astro_data1, 2)
    else:
        pair_iter = ((planet1, planet2) for planet1 in astro_data1 for planet2 in astro_data2)

    for planet1, planet2 in pair_iter:
        # 特別なポイント同士のアスペクトは除外
        special_points = [
            'アセンダント', 'ディセンダント',
            'MC（ミッドヘヴン）', 'IC（天底）',
            'バーテクス', 'パート・オブ・フォーチュン'
        ]
        if planet1['planet'] in special_points and planet2['planet'] in special_points:
            continue
        diff = abs(planet1['longitude'] - planet2['longitude'])
        diff = min(diff, 360 - diff)

        def _append_aspect(aspect_name: str, aspect_degree: float):
            record = {
                'planet1': planet1['planet'],
                'planet2': planet2['planet'],
                'aspect': aspect_name,
                'planet1_sign': planet1['sign'],
                'planet1_house': planet1['house'],
                'planet2_sign': planet2['sign'],
                'planet2_house': planet2['house'],
                'exact': diff,
                'orb': abs(diff - aspect_degree),
                'planet1_retrograde': planet1['retrograde'],
                'planet2_retrograde': planet2['retrograde']
            }
            if USE_USCS_PHASE:
                record.update(
                    build_phase_metrics(
                        float(planet1['longitude']),
                        float(planet2['longitude']),
                    )
                )
            aspects.append(record)

        # メジャーアスペクト
        for aspect, (aspect_degree, orb) in MAJOR_ASPECTS.items():
            if abs(diff - aspect_degree) <= orb:
                if (not SHOW_STRUCTURAL_NODE_ASPECTS) and is_structural_aspect(planet1['planet'], aspect, planet2['planet']):
                    continue
                _append_aspect(aspect, aspect_degree)
        # マイナーアスペクト
        if include_minor_aspects:
            for aspect, (aspect_degree, orb) in MINOR_ASPECTS.items():
                if abs(diff - aspect_degree) <= orb:
                    if (not SHOW_STRUCTURAL_NODE_ASPECTS) and is_structural_aspect(planet1['planet'], aspect, planet2['planet']):
                        continue
                    _append_aspect(aspect, aspect_degree)
    return aspects

def calculate_composite_aspects(astro_data, composite_aspects_def):
    """
    複合アスペクト（ヨッド、グランドクロス、Tスクエア、グランドトライン、
    キート、ミスティックレクタングル、レクタングル、スター、ヴェース）を検出します。
    COMPOSITE_SKIP に含まれる感受点は除外します。
    """
    composite_found = []
    normalized_data = normalize_node_objects(astro_data)
    # 標準的占星術慣習に基づくフィルタリング
    filtered = [p for p in normalized_data if p['planet'] not in COMPOSITE_SKIP]

    def angular_diff(p1, p2):
        diff = abs(p1['longitude'] - p2['longitude'])
        return min(diff, 360 - diff)

    def is_aspect(p1, p2, degree, orb):
        return abs(angular_diff(p1, p2) - degree) <= orb

    def unique_planets(planets):
        return len({p['planet'] for p in planets}) == len(planets)

    def as_name_list(planets):
        return [p['planet'] for p in planets]

    def add_pattern(type_name, planets, details):
        if not unique_planets(planets):
            return
        sorted_names = tuple(sorted(as_name_list(planets)))
        signature = (type_name, sorted_names)
        if signature in seen:
            return
        seen.add(signature)
        composite_found.append({
            'type': type_name,
            'planets': as_name_list(planets),
            'details': details,
        })

    seen = set()

    for jp_name, comp in composite_aspects_def.items():
        type_name = comp.get('type')
        orb = comp.get('orbs', 5)

        # ヨッド: 頂点1 → 2底辺がセクスタイル、頂点が両底辺とクインカンクス
        if type_name == 'yod':
            for p1, p2, apex in combinations(filtered, 3):
                if is_aspect(p1, p2, 60, orb) and is_aspect(apex, p1, 150, orb) and is_aspect(apex, p2, 150, orb):
                    add_pattern(jp_name, [apex, p1, p2], {'構成': '頂点1 + セクスタイル2'})
                if is_aspect(p1, apex, 60, orb) and is_aspect(p2, p1, 150, orb) and is_aspect(p2, apex, 150, orb):
                    add_pattern(jp_name, [p2, p1, apex], {'構成': '頂点1 + セクスタイル2'})
                if is_aspect(p2, apex, 60, orb) and is_aspect(p1, p2, 150, orb) and is_aspect(p1, apex, 150, orb):
                    add_pattern(jp_name, [p1, p2, apex], {'構成': '頂点1 + セクスタイル2'})

        # Tスクエア: オポジション + 両端にスクエアの頂点
        elif type_name == 't_square':
            for apex, p1, p2 in combinations(filtered, 3):
                if is_aspect(p1, p2, 180, orb) and is_aspect(apex, p1, 90, orb) and is_aspect(apex, p2, 90, orb):
                    add_pattern(jp_name, [apex, p1, p2], {'構成': '頂点1 + オポジション2'})
                if is_aspect(apex, p2, 180, orb) and is_aspect(p1, apex, 90, orb) and is_aspect(p1, p2, 90, orb):
                    add_pattern(jp_name, [p1, apex, p2], {'構成': '頂点1 + オポジション2'})
                if is_aspect(apex, p1, 180, orb) and is_aspect(p2, apex, 90, orb) and is_aspect(p2, p1, 90, orb):
                    add_pattern(jp_name, [p2, apex, p1], {'構成': '頂点1 + オポジション2'})

        # グランドトライン: 3天体がトライン
        elif type_name == 'grand_trine':
            for p1, p2, p3 in combinations(filtered, 3):
                if is_aspect(p1, p2, 120, orb) and is_aspect(p2, p3, 120, orb) and is_aspect(p1, p3, 120, orb):
                    add_pattern(jp_name, [p1, p2, p3], {'構成': 'トライン3本'})

        # グランドクロス: オポジション2本 + スクエア4本
        elif type_name == 'grand_cross':
            for p1, p2, p3, p4 in combinations(filtered, 4):
                planets = [p1, p2, p3, p4]
                pairs = [(i, j) for i in range(4) for j in range(i + 1, 4)]
                opposition_pairs = [
                    (i, j) for (i, j) in pairs if is_aspect(planets[i], planets[j], 180, orb)
                ]
                if len(opposition_pairs) != 2:
                    continue
                used_indices = {idx for pair in opposition_pairs for idx in pair}
                if len(used_indices) != 4:
                    continue
                square_count = sum(1 for (i, j) in pairs if is_aspect(planets[i], planets[j], 90, orb))
                if square_count >= 4:
                    add_pattern(jp_name, planets, {'構成': 'オポジション2本 + スクエア4本'})

        # キート: グランドトライン + テールがオポジション + セクスタイル2本
        elif type_name == 'kite':
            for p1, p2, p3 in combinations(filtered, 3):
                if not (is_aspect(p1, p2, 120, orb) and is_aspect(p2, p3, 120, orb) and is_aspect(p1, p3, 120, orb)):
                    continue
                trine = [p1, p2, p3]
                for tail in filtered:
                    if tail in trine:
                        continue
                    for apex in trine:
                        if is_aspect(tail, apex, 180, orb):
                            remain = [t for t in trine if t is not apex]
                            if len(remain) == 2 and is_aspect(tail, remain[0], 60, orb) and is_aspect(tail, remain[1], 60, orb):
                                add_pattern(jp_name, trine + [tail], {'構成': 'グランドトライン + オポジション1本 + セクスタイル2本'})

        # ミスティックレクタングル: オポジション2本 + セクスタイル2本 + トライン2本
        elif type_name == 'mystic_rectangle':
            for p1, p2, p3, p4 in combinations(filtered, 4):
                planets = [p1, p2, p3, p4]
                pairs = [(i, j) for i in range(4) for j in range(i + 1, 4)]
                opp = [(i, j) for (i, j) in pairs if is_aspect(planets[i], planets[j], 180, orb)]
                tri = [(i, j) for (i, j) in pairs if is_aspect(planets[i], planets[j], 120, orb)]
                sxt = [(i, j) for (i, j) in pairs if is_aspect(planets[i], planets[j], 60, orb)]
                if len(opp) == 2 and len(tri) == 2 and len(sxt) == 2:
                    add_pattern(jp_name, planets, {'構成': 'オポジション2本 + トライン2本 + セクスタイル2本'})

        # レクタングル（長方形）: オポジション2本 + スクエア2本 + セクスタイル2本
        elif type_name == 'rectangle':
            for p1, p2, p3, p4 in combinations(filtered, 4):
                planets = [p1, p2, p3, p4]
                pairs = [(i, j) for i in range(4) for j in range(i + 1, 4)]
                opp = [(i, j) for (i, j) in pairs if is_aspect(planets[i], planets[j], 180, orb)]
                sqr = [(i, j) for (i, j) in pairs if is_aspect(planets[i], planets[j], 90, orb)]
                sxt = [(i, j) for (i, j) in pairs if is_aspect(planets[i], planets[j], 60, orb)]
                if len(opp) == 2 and len(sqr) == 2 and len(sxt) == 2:
                    add_pattern(jp_name, planets, {'構成': 'オポジション2本 + スクエア2本 + セクスタイル2本'})

        # スター（ダビデの星）: グランドトライン2つが重なる6天体
        elif type_name == 'star':
            for combo in combinations(filtered, 6):
                planets = list(combo)
                pairs = [(i, j) for i in range(6) for j in range(i + 1, 6)]
                opp_count = sum(1 for (i, j) in pairs if is_aspect(planets[i], planets[j], 180, orb))
                tri_count = sum(1 for (i, j) in pairs if is_aspect(planets[i], planets[j], 120, orb))
                sxt_count = sum(1 for (i, j) in pairs if is_aspect(planets[i], planets[j], 60, orb))
                # 6本のトライン + 6本のセクスタイル + 3本のオポジション（理想形）
                if tri_count >= 6 and sxt_count >= 6 and opp_count >= 3:
                    add_pattern(jp_name, planets, {'構成': 'ダビデの星（グランドトライン2重）'})

        # ヴェース（花瓶）: Tスクエア + セクスタイル2本（ソフトな出口）
        elif type_name == 'vase':
            for apex, p1, p2 in combinations(filtered, 3):
                if not (is_aspect(p1, p2, 180, orb) and is_aspect(apex, p1, 90, orb) and is_aspect(apex, p2, 90, orb)):
                    continue
                for outlet in filtered:
                    if outlet in [apex, p1, p2]:
                        continue
                    if is_aspect(outlet, p1, 60, orb) and is_aspect(outlet, p2, 60, orb):
                        add_pattern(jp_name, [apex, p1, p2, outlet], {'構成': 'Tスクエア + セクスタイル出口1'})

    return dedupe_composite_patterns(composite_found)
def get_aspect_between(p1, p2, orb):
    """
    二つの惑星データからアスペクトを判定（使いたい場合に実装）。
    """
    diff = abs(p1['longitude'] - p2['longitude'])
    diff = min(diff, 360 - diff)
    aspects = []
    # メジャーアスペクト
    for aspect, (degree, aspect_orb) in MAJOR_ASPECTS.items():
        if abs(diff - degree) <= orb:
            aspects.append({'aspect': aspect, 'orb': abs(diff - degree)})
    # マイナーアスペクト
    for aspect, (degree, aspect_orb) in MINOR_ASPECTS.items():
        if abs(diff - degree) <= orb:
            aspects.append({'aspect': aspect, 'orb': abs(diff - degree)})
    return aspects

def print_chart(chart, chart_name):
    """
    チャートの情報を出力します。
    """
    print(f"\n--- {chart_name} ---")
    for planet in chart:
        retro_text = "（逆行）" if planet.get('retrograde', False) else ""
        print(f"{planet['planet']}{retro_text} が {planet['sign']} {planet['longitude']:.2f}°、"
              f"ハウス{planet['house']}に位置。")

def print_aspects(aspects, aspect_name):
    """
    アスペクトの情報を出力します。
    """
    print(f"\n--- {aspect_name} ---")
    if not aspects:
        print("アスペクトは検出されませんでした。")
        return
    for aspect in aspects:
        planet1_retro = "（逆行）" if aspect.get('planet1_retrograde', False) else ""
        planet2_retro = "（逆行）" if aspect.get('planet2_retrograde', False) else ""
        print(
            f"{aspect['planet1']}{planet1_retro}（{aspect['planet1_sign']}・H{aspect['planet1_house']}）と "
            f"{aspect['planet2']}{planet2_retro}（{aspect['planet2_sign']}・H{aspect['planet2_house']}）が "
            f"{aspect['aspect']}。オーブ: {aspect['orb']:.2f}° (実際の角度: {aspect['exact']:.2f}°)"
        )

def print_composite_aspects(composite_aspects, chart_name):
    """
    複合アスペクトの情報を出力します。
    """
    print(f"\n--- {chart_name}の複合アスペクト ---")
    if not composite_aspects:
        print("複合アスペクトは見つかりませんでした。")
        return
    for composite in composite_aspects:
        type_ = composite['type']
        planets = '、'.join(composite['planets'])
        print(f"{type_}: {planets}")
        for key, value in composite['details'].items():
            if isinstance(value, list):
                for item in value:
                    print(f"  - {key}: {item}")
            else:
                print(f"  - {key}: {value}")

def print_house_cusps(cusps, chart_name):
    """
    ハウスカスプの度数を出力します。
    """
    print(f"\n--- {chart_name}のハウスカスプ ---")
    for i in range(1, 13):
        cusp_degree = cusps[i] % 360.0
        sign = int(cusp_degree // 30) % 12
        print(f"第{i}ハウス: {cusp_degree:.2f}°（{SIGNS[sign]}）")

def print_sun_position(chart, chart_name):
    """
    太陽の位置だけ簡易表示。
    """
    for planet in chart:
        if planet['planet'] == '太陽':
            retro_text = "（逆行）" if planet.get('retrograde', False) else ""
            print(f"\n--- {chart_name}の太陽 ---")
            print(f"サイン: {planet['sign']}")
            print(f"経度: {planet['longitude']:.2f}°")
            print(f"ハウス: {planet['house']}")
            print(f"逆行フラグ: {retro_text if retro_text else 'なし'}")


def save_results_to_text(
    charts: dict,
    aspects_sets: list,
    composite_sets: list,
    filepath: str,
) -> None:
    """
    チャート・アスペクト・複合アスペクトの結果をテキストファイルに保存します。

    Args:
        charts: {'チャート名': chart_data} の辞書
        aspects_sets: [(aspects_list, '見出し文字列'), ...] のリスト
        composite_sets: [(composite_list, '見出し文字列'), ...] のリスト
        filepath: 保存先ファイルパス
    """
    lines = []
    lines.append(f"占星術チャート結果レポート")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)

    for chart_name, chart in charts.items():
        lines.append(f"\n--- {chart_name} ---")
        for planet in chart:
            retro_text = "（逆行）" if planet.get('retrograde', False) else ""
            lines.append(
                f"  {planet['planet']}{retro_text}: {planet['sign']} "
                f"{planet['longitude']:.2f}°  H{planet['house']}"
            )

    for aspects, title in aspects_sets:
        lines.append(f"\n--- {title} ---")
        if not aspects:
            lines.append("  アスペクトは検出されませんでした。")
        else:
            for asp in aspects:
                r1 = "（逆行）" if asp.get('planet1_retrograde') else ""
                r2 = "（逆行）" if asp.get('planet2_retrograde') else ""
                lines.append(
                    f"  {asp['planet1']}{r1}({asp['planet1_sign']}・H{asp['planet1_house']}) "
                    f"× {asp['planet2']}{r2}({asp['planet2_sign']}・H{asp['planet2_house']}): "
                    f"{asp['aspect']}  オーブ{asp['orb']:.2f}°"
                )

    for composites, title in composite_sets:
        lines.append(f"\n--- {title} ---")
        if not composites:
            lines.append("  複合アスペクトは検出されませんでした。")
        else:
            for comp in composites:
                planets_str = "、".join(comp['planets'])
                lines.append(f"  {comp['type']}: {planets_str}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"[SAVE] 結果を保存しました: {filepath}")

# 占い師文体テンプレート（差分追加）
def _orb_label(orb: float) -> str:
    """オーブの密度をラベルで返す（差分追加）。"""
    if orb <= 1.0:
        return "ほぼ正確な（非常にタイトな）"
    elif orb <= 3.0:
        return "タイトな"
    elif orb <= 5.0:
        return "中程度の"
    else:
        return "緩やかな"

_HOUSE_THEME = {
    1:  "自己・外見・第一印象",
    2:  "価値観・お金・所有",
    3:  "コミュニケーション・兄弟・短距離移動",
    4:  "家庭・ルーツ・内面の基盤",
    5:  "創造・恋愛・自己表現・遊び",
    6:  "健康・日課・奉仕・仕事の細部",
    7:  "パートナーシップ・対人関係・契約",
    8:  "変容・共有資源・死と再生・深層心理",
    9:  "哲学・高等教育・海外・信念",
    10: "社会的地位・キャリア・公の顔",
    11: "友人・コミュニティ・夢と理想",
    12: "潜在意識・隠れた敵・孤独・霊性",
}

_SIGN_META = {
    "牡羊座":  {"element": "火", "mode": "活動", "keyword": "行動力と開拓精神"},
    "牡牛座":  {"element": "地", "mode": "固定", "keyword": "安定と感覚的な豊かさ"},
    "双子座":  {"element": "風", "mode": "柔軟", "keyword": "知的好奇心と多様性"},
    "蟹座":    {"element": "水", "mode": "活動", "keyword": "感情の深さと養育"},
    "獅子座":  {"element": "火", "mode": "固定", "keyword": "誇りと創造的な自己表現"},
    "乙女座":  {"element": "地", "mode": "柔軟", "keyword": "分析力と誠実な奉仕"},
    "天秤座":  {"element": "風", "mode": "活動", "keyword": "調和と美的センス"},
    "蠍座":    {"element": "水", "mode": "固定", "keyword": "深層への洞察と変容"},
    "射手座":  {"element": "火", "mode": "柔軟", "keyword": "探求心と自由への渇望"},
    "山羊座":  {"element": "地", "mode": "活動", "keyword": "忍耐と社会的達成"},
    "水瓶座":  {"element": "風", "mode": "固定", "keyword": "革新と人類への貢献"},
    "魚座":    {"element": "水", "mode": "柔軟", "keyword": "共感と霊的な溶解"},
}

_PLANET_MEANING = {
    "太陽":   "核となる自己・意志・生命力",
    "月":     "感情・本能・安心感の源",
    "水星":   "思考・言語・情報処理",
    "金星":   "愛・美・喜び・価値観",
    "火星":   "行動力・情熱・欲求・勇気",
    "木星":   "拡大・幸運・哲学・成長",
    "土星":   "制限・責任・試練・構造",
    "天王星": "革命・自由・突然の変化",
    "海王星": "幻想・霊性・溶解・理想",
    "冥王星": "変容・破壊と再生・権力",
    "ドラゴンヘッド": "魂の成長方向・カルマ的テーマ",
    "キロン": "傷と癒し・師匠としての痛み",
    "リリス": "抑圧された欲求・本能の影",
    "セレス": "養育・豊穣・喪失と受容",
    "ジュノー": "対等なパートナーシップ・契約",
    "ベスタ": "献身・純粋な集中力・神聖な炎",
    "パラス": "知恵・戦略・正義の感覚",
}

_PLANET_IN_HOUSE = {
    "太陽": ["", "{planet}が第1ハウスに在ります。{h_theme}の場で存在感が強く、人生を自ら切り拓く意志が前面に出ます。", "{planet}が第2ハウスに在ります。{h_theme}を通して自己価値を育て、現実的な安定を築くことがテーマです。", "{planet}が第3ハウスに在ります。{h_theme}の場で言葉と学びが輝き、知的な発信が人生を開きます。", "{planet}が第4ハウスに在ります。{h_theme}に根を張ることで、本来の生命力が安定して発揮されます。", "{planet}が第5ハウスに輝きます。創造・恋愛・遊びの領域で本来の輝きが花開き、表現すること自体が生きがいとなります。", "{planet}が第6ハウスに在ります。{h_theme}を整えるほど自己効力感が高まり、実務の中で光を放ちます。", "{planet}が第7ハウスに在ります。{h_theme}を通じて自己理解が深まり、関係性の中で使命が明確になります。", "{planet}が第8ハウスに在ります。{h_theme}の深みで大きな変容を経験し、再生を繰り返して強くなります。", "{planet}が第9ハウスに在ります。{h_theme}を探求することで視野が広がり、人生哲学が輝きます。", "{planet}が第10ハウスに在ります。{h_theme}で評価されやすく、社会的役割を果たすことが自己実現に直結します。", "{planet}が第11ハウスに在ります。{h_theme}の場で理想を共有し、未来志向のネットワークから力を得ます。", "{planet}が第12ハウスに在ります。{h_theme}の領域で静かな献身が育ち、内面的な統合が人生を導きます。"],
    "月": ["", "{planet}が第1ハウスに在ります。感情が表情や雰囲気に出やすく、{h_theme}の変化に敏感です。", "{planet}が第2ハウスに在ります。{h_theme}の安定が心の安定に直結し、安心できる基盤づくりを求めます。", "{planet}が第3ハウスに在ります。{h_theme}を通じて気持ちを整理し、対話が心の栄養になります。", "{planet}が第4ハウスに在ります。{h_theme}が人生の最重要テーマとなり、内なる居場所づくりが鍵です。", "{planet}が第5ハウスに在ります。{h_theme}の場で喜びを感じ、愛情表現が心を満たします。", "{planet}が第6ハウスに在ります。{h_theme}を整えることで心身のリズムが回復しやすくなります。", "{planet}が第7ハウスに在ります。{h_theme}で感情が揺れやすく、対話を通じた共感が癒しになります。", "{planet}が第8ハウスに在ります。{h_theme}で感情の深層が刺激され、強い結びつきを求めます。", "{planet}が第9ハウスに在ります。{h_theme}が心を拡張し、旅や学びが感情を浄化します。", "{planet}が第10ハウスに在ります。{h_theme}に感情が反応しやすく、公的役割への責任感が高まります。", "{planet}が第11ハウスに在ります。{h_theme}を通じて仲間意識が育ち、理想を共有する場に安心します。", "{planet}が第12ハウスに在ります。{h_theme}で無意識の感受性が高まり、休息と浄化が重要です。"],
    "水星": ["", "{planet}が第1ハウスに在ります。{h_theme}で機転の良さが際立ち、言葉で道を切り開きます。", "{planet}が第2ハウスに在ります。{h_theme}に関する情報処理能力が高く、実利的な判断が得意です。", "{planet}が第3ハウスに在ります。{h_theme}で本領発揮し、学習・執筆・会話に強みが出ます。", "{planet}が第4ハウスに在ります。{h_theme}について深く考え、家族観や記憶が思考の土台になります。", "{planet}が第5ハウスに在ります。{h_theme}で創造的な発想が冴え、言葉遊びや表現力が光ります。", "{planet}が第6ハウスに在ります。{h_theme}における分析と改善が得意で、実務での精度が高い配置です。", "{planet}が第7ハウスに在ります。{h_theme}で交渉力が活き、対話から最適解を導きます。", "{planet}が第8ハウスに在ります。{h_theme}の領域で洞察が深まり、心理や秘密を読む力を持ちます。", "{planet}が第9ハウスに在ります。{h_theme}に知性が向かい、専門研究や哲学的思考に適性があります。", "{planet}が第10ハウスに在ります。{h_theme}で情報発信力が評価され、仕事での言語能力が武器です。", "{planet}が第11ハウスに在ります。{h_theme}をネットワーク化し、仲間と知を共有して成果を出します。", "{planet}が第12ハウスに在ります。{h_theme}で直観的な思考が育ち、内省や執筆で才能が開きます。"],
    "金星": ["", "{planet}が第1ハウスに在ります。{h_theme}に魅力が宿り、自然体で人を惹きつけます。", "{planet}が第2ハウスに在ります。{h_theme}に喜びを見出し、美意識と豊かさを育てます。", "{planet}が第3ハウスに在ります。{h_theme}で愛嬌のある対話が生まれ、言葉が魅力になります。", "{planet}が第4ハウスに在ります。{h_theme}で美と安心を求め、居心地のよい空間づくりが得意です。", "{planet}が第5ハウスに在ります。{h_theme}で恋愛運と創作運が高まり、楽しみながら才能が花開きます。", "{planet}が第6ハウスに在ります。{h_theme}に調和をもたらし、丁寧な日常が幸福感を育てます。", "{planet}が第7ハウスに在ります。{h_theme}で愛と協調がテーマとなり、良縁を引き寄せやすい配置です。", "{planet}が第8ハウスに在ります。{h_theme}で深い結びつきを求め、濃密な愛情体験を通じて変容します。", "{planet}が第9ハウスに在ります。{h_theme}で審美眼が広がり、異文化や学問に喜びを見出します。", "{planet}が第10ハウスに在ります。{h_theme}で好感度と評価が高まり、対人調整力が仕事で活きます。", "{planet}が第11ハウスに在ります。{h_theme}で友愛が広がり、共通の理想を持つ仲間に恵まれます。", "{planet}が第12ハウスに在ります。{h_theme}で静かな優しさが育ち、見えない形で愛を注ぎます。"],
    "火星": ["", "{planet}が第1ハウスに在ります。{h_theme}で行動力が前面に出て、先陣を切る役割を担います。", "{planet}が第2ハウスに在ります。{h_theme}で稼ぐ力と守る力が強く、現実面で粘り強く戦います。", "{planet}が第3ハウスに在ります。{h_theme}で発言に勢いが宿り、議論や交渉で突破力を発揮します。", "{planet}が第4ハウスに在ります。{h_theme}で防衛本能が強まり、身内を守るための闘志が湧きます。", "{planet}が第5ハウスに在ります。{h_theme}で情熱が燃え、恋愛や創作に積極性が出ます。", "{planet}が第6ハウスに在ります。{h_theme}で実行力が高く、課題処理のスピードが武器になります。", "{planet}が第7ハウスに在ります。{h_theme}で競争心が刺激され、対人関係で主導権争いが起こりやすい配置です。", "{planet}が第8ハウスに在ります。{h_theme}で強い執着と突破力が生まれ、極限状況で真価を発揮します。", "{planet}が第9ハウスに在ります。{h_theme}へ向かう情熱が強く、信念のために行動する力があります。", "{planet}が第10ハウスに在ります。{h_theme}で野心が高まり、キャリアで結果を出す推進力になります。", "{planet}が第11ハウスに在ります。{h_theme}で改革への意欲が高く、集団で先導的に動きます。", "{planet}が第12ハウスに在ります。{h_theme}で怒りや欲求が内面化しやすく、意識的な発散が重要です。"],
    "木星": ["", "{planet}が第1ハウスに在ります。{h_theme}で楽観性と包容力が広がり、存在そのものが希望を運びます。", "{planet}が第2ハウスに在ります。{h_theme}で発展運が働き、豊かさを拡大しやすい配置です。", "{planet}が第3ハウスに在ります。{h_theme}で学びと交流が発展し、知識が幸運を呼び込みます。", "{planet}が第4ハウスに在ります。{h_theme}で守護が働き、心の基盤を大きく育てていきます。", "{planet}が第5ハウスに在ります。{h_theme}で創造性と喜びが拡大し、恋愛運や表現力に追い風です。", "{planet}が第6ハウスに在ります。{h_theme}で成長機会が増え、仕事や健康習慣の改善が実を結びます。", "{planet}が第7ハウスに在ります。{h_theme}で良縁や援助に恵まれ、協力関係から発展が生まれます。", "{planet}が第8ハウスに在ります。{h_theme}で深い学びが拡大し、心理的・経済的な共有で恩恵があります。", "{planet}が第9ハウスに在ります。{h_theme}で最も力を発揮し、探求・教育・海外運に大きな追い風があります。", "{planet}が第10ハウスに在ります。{h_theme}で社会的成功運が高まり、公的評価を得やすくなります。", "{planet}が第11ハウスに在ります。{h_theme}で夢の実現力が高く、人脈が発展の鍵になります。", "{planet}が第12ハウスに在ります。{h_theme}で見えない加護が働き、慈愛と精神性が深まります。"],
    "土星": ["", "{planet}が第1ハウスに在ります。{h_theme}で責任感が強く、自己鍛錬を通じて信頼を築きます。", "{planet}が第2ハウスに在ります。{h_theme}で堅実さが求められ、時間をかけて確かな資産を形成します。", "{planet}が第3ハウスに在ります。{h_theme}で思考が慎重になり、学びの継続が大きな成果を生みます。", "{planet}が第4ハウスに在ります。{h_theme}で課題意識が強まり、家族や基盤への責任を学びます。", "{planet}が第5ハウスに在ります。{h_theme}で自己表現に真剣さが増し、努力の末に創造が実を結びます。", "{planet}が第6ハウスに在ります。{h_theme}で規律と忍耐が試され、職人的な完成度へ向かいます。", "{planet}が第7ハウスに在ります。{h_theme}で対人責任が重くなり、成熟した関係を築く学びが進みます。", "{planet}が第8ハウスに在ります。{h_theme}で深い恐れと向き合い、手放しと再構築を学びます。", "{planet}が第9ハウスに在ります。{h_theme}で信念を現実化する試練があり、学問と実践の一致が鍵です。", "{planet}が第10ハウスに在ります。{h_theme}で社会的責任が強まり、遅咲きでも大きな実績を残せます。", "{planet}が第11ハウスに在ります。{h_theme}で理想実現に時間を要しますが、長期的な信頼網を築けます。", "{planet}が第12ハウスに在ります。{h_theme}で内的課題と向き合い、孤独な鍛錬が精神的成熟をもたらします。"],
}

_ASPECT_INTERP = {
    'コンジャンクション': (
        "{orb_label}コンジャンクション：{p1}（{s1}・H{h1}）と{p2}（{s2}・H{h2}）が一点に融合しています。"
        "{h1_theme}と{h2_theme}の領域が渾然一体となり、強烈な集中力を生み出しています。"
    ),
    'オポジション': (
        "{orb_label}オポジション：{p1}（{s1}・H{h1}）と{p2}（{s2}・H{h2}）が向かい合います。"
        "{h1_theme}と{h2_theme}の軸で引き合いが生まれ、{s1_kw}と{s2_kw}を統合する成熟が求められます。"
    ),
    'トライン': (
        "{orb_label}トライン：{p1}（{s1}・H{h1}）と{p2}（{s2}・H{h2}）が美しく調和。"
        "{h1_theme}と{h2_theme}に自然な追い風が流れ、{s1_kw}の資質が才能として活きます。"
    ),
    'スクエア': (
        "{orb_label}スクエア：{p1}（{s1}・H{h1}）と{p2}（{s2}・H{h2}）の間に摩擦が走ります。"
        "{h1_theme}と{h2_theme}の衝突が課題を照らし、鍛錬を通して大きな成長を促します。"
    ),
    'セクスタイル': (
        "{orb_label}セクスタイル：{p1}（{s1}・H{h1}）と{p2}（{s2}・H{h2}）が協調しています。"
        "{h1_theme}と{h2_theme}を結ぶ機会が訪れ、主体的に動くほど実りが増します。"
    ),
    'クインカンクス（150°）': (
        "{orb_label}クインカンクス：{p1}（{s1}・H{h1}）と{p2}（{s2}・H{h2}）は調整を求める角度です。"
        "{h1_theme}と{h2_theme}の再調律を行うことで、新しい均衡点が見えてきます。"
    ),
}
_COMPOSITE_INTERP = {
    'ヨッド':             "「神の指」とも呼ばれるヨッドが形成されています（{planets}）。特別な使命や運命的な課題を示し、頂点の天体が示す領域で深い変容が求められます。",
    'グランドトライン':   "3つの天体（{planets}）が大きな三角形を描くグランドトラインが見られます。豊かな才能と恵みの流れがありますが、その安定ゆえに成長への動機が失われやすい面もあります。",
    'Tスクエア':          "Tスクエア（{planets}）が示す強い緊張があります。頂点の天体が示す課題に全力で取り組むことで、大きな力が解放されます。",
    'グランドクロス':     "4つの天体（{planets}）が十字を描くグランドクロスが形成されています。強大な緊張とプレッシャーを抱えますが、それを統合できたとき圧倒的な力となります。",
    'キート':             "凧の形を描くキート（{planets}）があります。グランドトラインの恵みに方向性と推進力が加わり、才能が現実世界へ発揮されやすくなります。",
    'ミスティックレクタングル': "神秘的な長方形（{planets}）が形成されています。調和と緊張が絶妙なバランスを保ちながら、霊的・創造的な統合を促します。",
    'レクタングル':       "レクタングル（{planets}）が見られます。実践的な緊張と協調が組み合わさり、粘り強く取り組む力をもたらします。",
    'スター':             "ダビデの星とも呼ばれる6天体のスター（{planets}）が形成されています。多面的な才能と強い霊的・社会的な影響力を示します。",
    'ヴェース':           "ヴェース（{planets}）が示すパターンがあります。Tスクエアの緊張に出口が与えられ、問題解決への道筋が自然に開きます。",
}


MAIN_INTERPRET_PLANETS = {"太陽", "月", "アセンダント", "水星", "金星", "火星", "木星", "土星"}

PLANET_ARCHETYPE = {
    "太陽": "意志と自己実現",
    "月": "感情と安心パターン",
    "アセンダント": "対外的な振る舞い",
    "水星": "思考と言語化",
    "金星": "価値観と親和性",
    "火星": "行動と闘争本能",
    "木星": "拡大と信念",
    "土星": "責任と成熟",
}

SIGN_ARCHETYPE = {
    sign: meta["keyword"] for sign, meta in _SIGN_META.items()
}

HOUSE_ARCHETYPE = {
    house: theme for house, theme in _HOUSE_THEME.items()
}

PLANET_SIGN_MEANING = {
    ("月", "獅子座"): "感情が誇りと創造欲を通じて発露し、承認される場で心が温まります",
    ("水星", "射手座"): "思考は大局観と思想性を重視し、意味を語る言葉に強みが出ます",
    ("金星", "山羊座"): "愛情は誠実さと責任を伴って表現され、長期的な信頼を重視します",
    ("火星", "牡羊座"): "行動力が先陣を切る形で現れ、瞬発力と突破力が武器になります",
    ("木星", "魚座"): "成長は共感と精神性を媒介に拡大し、包容力が幸運を招きます",
    ("土星", "山羊座"): "責任感と構造化能力が高まり、遅くても確実な成果を築きます",
    ("太陽", "蠍座"): "意志が深層・変容・極限のテーマへ向かい、真実を掘り当てる力が高まります",
    ("月", "蟹座"): "感情は保護と養育の欲求を強く帯び、安心できる居場所で回復します",
    ("水星", "双子座"): "思考は多面的で俊敏になり、比較・翻訳・接続の才が伸びます",
    ("金星", "天秤座"): "愛情と価値観は調和と美意識を求め、関係性の質を整える力になります",
    ("火星", "蠍座"): "行動力は一点集中と底力として現れ、決めた目標を徹底的に遂行します",
    ("木星", "射手座"): "成長意欲は探求と理想へ開かれ、学びを拡張して可能性を広げます",
    ("アセンダント", "牡羊座"): "第一印象は率直で先駆的に映り、開始力のある人物像を作ります",
}

PLANET_HOUSE_MEANING = {
    ("太陽", 9): "自己実現は哲学・信念・高次学習の探求を通じて進みます",
    ("月", 7): "感情安定は対話とパートナーシップの質に強く連動します",
    ("水星", 10): "言語化能力が社会的評価へ直結し、仕事で知性を発揮します",
    ("金星", 5): "喜びと魅力は創造・恋愛・自己表現の領域で自然に花開きます",
    ("火星", 6): "実務と習慣の改善に闘志が向き、鍛錬で結果を出します",
}

PLANET_PAIR_MEANING = {
    frozenset(["太陽", "月"]): "意志と感情の接続",
    frozenset(["太陽", "土星"]): "自己肯定感と責任の再編",
    frozenset(["水星", "月"]): "思考と感情翻訳の回路",
    frozenset(["金星", "火星"]): "愛情と欲求の推進力",
    frozenset(["木星", "土星"]): "拡大と収束のバランス",
    frozenset(["月", "リリス"]): "安心欲求と抑圧本能の接触",
    frozenset(["火星", "木星"]): "挑戦心と拡張意欲の増幅",
    frozenset(["月", "冥王星"]): "感情の深層変容と再生力",
    frozenset(["月", "天王星"]): "情緒の自由化と変化衝動",
}

ASPECT_MEANING = {
    "コンジャンクション": "二つの力が融合し、テーマが過剰にも才能にもなりやすい角度",
    "トライン": "自然に循環し、努力感が少ないまま才能化しやすい角度",
    "セクスタイル": "機会を掴むほど協力作用が高まる角度",
    "スクエア": "摩擦が課題を可視化し、成長圧を生む角度",
    "オポジション": "両極の緊張から客観性と統合力を育てる角度",
    "クインカンクス（150°）": "調整を繰り返しながら最適化を迫る角度",
}


def normalize_node_name(name: str) -> str:
    """ノード系名称を正規化キーへ変換。"""
    rule = NODE_NORMALIZE_RULES.get(name)
    return rule["alias_group"] if rule else name


def normalize_planet_name_for_display(name: str) -> str:
    """表示名を NODE_MODE に応じて整形。"""
    rule = NODE_NORMALIZE_RULES.get(name)
    if not rule:
        return name
    if NODE_MODE == "merged":
        return rule["merged"]
    return name


def normalize_planet_name_for_patterns(name: str) -> str:
    """複合配置の重複判定に使う正規化名。"""
    if name in NODE_NORMALIZE_RULES:
        return NODE_NORMALIZE_RULES[name]["alias_group"]
    return name


def is_structural_aspect(planet1: str, aspect: str, planet2: str) -> bool:
    """定義上ほぼ必然のノード系アスペクトかを判定。"""
    n1, n2 = normalize_node_name(planet1), normalize_node_name(planet2)
    key = tuple(sorted([n1, n2]))
    return (key[0], aspect, key[1]) in STRUCTURAL_ASPECT_KEYS


def normalize_node_objects(chart: list[dict]) -> list[dict]:
    """NODE_MODE に応じてノード系の表示対象を統合する。"""
    if NODE_MODE not in {"true", "mean", "merged"}:
        raise ValueError(f"NODE_MODE must be one of true|mean|merged, got: {NODE_MODE}")

    grouped: dict[str, dict] = {}
    passthrough: list[dict] = []
    for obj in chart:
        rule = NODE_NORMALIZE_RULES.get(obj.get("planet"))
        if not rule:
            passthrough.append(obj)
            continue
        key = rule["alias_group"]
        if NODE_MODE == "merged":
            candidate = dict(obj)
            candidate["planet"] = rule["merged"]
            grouped.setdefault(key, candidate)
            continue
        if rule["mode"] == NODE_MODE:
            grouped[key] = obj

    return passthrough + list(grouped.values())


def _aspect_display_key(asp: dict) -> tuple:
    p1 = normalize_planet_name_for_patterns(asp.get("planet1"))
    p2 = normalize_planet_name_for_patterns(asp.get("planet2"))
    ordered = tuple(sorted([p1, p2]))
    return (ordered[0], asp.get("aspect"), ordered[1])


def dedupe_aspects(aspects: list[dict]) -> list[dict]:
    """同義に近いアスペクトを表示キー単位で集約（最小オーブ優先）。"""
    best: dict[tuple, dict] = {}
    for asp in aspects:
        if (not SHOW_STRUCTURAL_NODE_ASPECTS) and is_structural_aspect(asp.get("planet1"), asp.get("aspect"), asp.get("planet2")):
            continue
        key = _aspect_display_key(asp)
        prev = best.get(key)
        if not prev or asp.get("orb", 999) < prev.get("orb", 999):
            chosen = dict(asp)
            chosen["planet1"] = normalize_planet_name_for_display(chosen.get("planet1"))
            chosen["planet2"] = normalize_planet_name_for_display(chosen.get("planet2"))
            best[key] = chosen
    return sorted(best.values(), key=lambda x: (x.get("orb", 999), x.get("aspect", "")))


def dedupe_composite_patterns(composites: list[dict]) -> list[dict]:
    """複合配置をノード近似重複込みで代表1件に集約。"""
    best: dict[tuple, dict] = {}
    for comp in composites:
        normalized_planets = sorted(normalize_planet_name_for_patterns(p) for p in comp.get("planets", []))
        key = (comp.get("type"), tuple(normalized_planets))
        prev = best.get(key)
        if prev is None or len(comp.get("planets", [])) < len(prev.get("planets", [])):
            item = dict(comp)
            item["planets"] = [normalize_planet_name_for_display(p) for p in comp.get("planets", [])]
            best[key] = item
    return list(best.values())


def summarize_element_mode_balance(chart: list[dict]) -> str:
    """主要天体を中心にエレメント/モード偏りを要約する。"""
    targets = [p for p in chart if p.get("planet") in MAIN_INTERPRET_PLANETS and p.get("sign") in _SIGN_META]
    if not targets:
        return "主要天体のサイン情報が不足しているため、エレメント/モード偏りは判定できません。"

    element_count = {"火": 0, "地": 0, "風": 0, "水": 0}
    mode_count = {"活動": 0, "固定": 0, "柔軟": 0}
    for p in targets:
        meta = _SIGN_META[p["sign"]]
        element_count[meta["element"]] += 1
        mode_count[meta["mode"]] += 1

    top_element = max(element_count, key=element_count.get)
    top_mode = max(mode_count, key=mode_count.get)
    implication = {
        ("水", "固定"): "感情の深掘りと粘り強さが強く、極端化を自己観察で調整すると大きな集中力になります",
        ("地", "活動"): "現実化と実行管理に強く、目標を構造化すると成果が加速します",
        ("風", "柔軟"): "思考と対話の回転が速く、情報過多を選別できると知性が洗練されます",
        ("火", "活動"): "推進力が高く、短期勝負に強い一方で休息設計が鍵になります",
    }.get((top_element, top_mode), "偏りは個性の核です。逆側の要素を意識的に補うと安定します")

    return (
        f"エレメント偏り: 火{element_count['火']} / 地{element_count['地']} / 風{element_count['風']} / 水{element_count['水']}。"
        f"モード偏り: 活動{mode_count['活動']} / 固定{mode_count['固定']} / 柔軟{mode_count['柔軟']}。"
        f"現在は『{top_element} × {top_mode}』が優勢で、{implication}。"
    )


def detect_stellium(chart: list[dict]) -> list[str]:
    """主要天体3つ以上の同一サイン/ハウス集中を検出する。"""
    major = [p for p in chart if p.get("planet") in MAIN_INTERPRET_PLANETS]
    sign_map: dict[str, list[str]] = {}
    house_map: dict[int, list[str]] = {}
    for p in major:
        sign_map.setdefault(p.get("sign"), []).append(p["planet"])
        house_map.setdefault(p.get("house"), []).append(p["planet"])

    outputs: list[str] = []
    for sign, planets in sign_map.items():
        uniq = sorted(set(planets))
        if sign and len(uniq) >= 3:
            outputs.append(f"{sign}に{', '.join(uniq)}が集中し、{SIGN_ARCHETYPE.get(sign, sign)}のテーマが人生全体を牽引します")
    for house, planets in house_map.items():
        uniq = sorted(set(planets))
        if house and len(uniq) >= 3:
            outputs.append(f"第{house}ハウスに{', '.join(uniq)}が集中し、{HOUSE_ARCHETYPE.get(house, '')}の領域が重要課題になります")
    return outputs


def detect_house_cluster(chart: list[dict]) -> list[str]:
    """同一ハウスへの主要天体集中を抽出する。"""
    major = [p for p in chart if p.get("planet") in MAIN_INTERPRET_PLANETS]
    house_map: dict[int, list[str]] = {}
    for p in major:
        house_map.setdefault(p.get("house"), []).append(p["planet"])
    outputs: list[str] = []
    for house, planets in house_map.items():
        uniq = sorted(set(planets))
        if house and len(uniq) >= 3:
            outputs.append(f"第{house}ハウス集中（{', '.join(uniq)}）")
    return outputs


def synthesize_planet_sign(p: dict, suppress_redundant: bool = False) -> str:
    """Planet × Sign の読みを返す。"""
    planet = p.get("planet", "")
    sign = p.get("sign", "")
    if suppress_redundant:
        return f"{planet}は{sign}らしい感性を内側に持っています"
    return PLANET_SIGN_MEANING.get(
        (planet, sign),
        f"{PLANET_ARCHETYPE.get(planet, planet)}が{SIGN_ARCHETYPE.get(sign, sign)}として表れます",
    )


def synthesize_planet_house(p: dict, recent_templates: dict[str, str] | None = None) -> str:
    """Planet × House の読みを返す。"""
    planet = p.get("planet", "")
    house = p.get("house", 0)
    preset = PLANET_HOUSE_MEANING.get((planet, house))
    if preset:
        return preset
    theme = HOUSE_ARCHETYPE.get(house, "")
    if recent_templates is None:
        return f"第{house}ハウス（{theme}）で、その力が具体化しやすいでしょう"
    template = choose_non_repeating_template(HOUSE_SENTENCE_VARIATIONS, "house_sentence", recent_templates)
    return template.format(house=house, theme=theme)


ENDING_VARIATIONS = [
    "この配置は、実践の中で輪郭がはっきりしてきます。",
    "取り組みを重ねるほど、この資質の使い方が洗練されます。",
    "経験を通じて強みが育ちやすい配置です。",
    "日々の選択の積み重ねが、この力を本領へ導きます。",
]

HOUSE_SENTENCE_VARIATIONS = [
    "第{house}ハウス（{theme}）で、その力が具体化しやすいでしょう。",
    "第{house}ハウス（{theme}）の場面で、本領が見えやすくなります。",
    "第{house}ハウス（{theme}）を通じて、資質が育ちやすい配置です。",
]

ACTION_HINT_VARIATIONS = [
    "活かし方のヒント: {hint}",
    "実践のコツ: {hint}",
    "行動提案: {hint}",
]


def choose_non_repeating_template(candidates: list[str], key: str, recent: dict[str, str | int]) -> str:
    if not candidates:
        return ""
    prev = recent.get(key)
    count_key = f"{key}__count"
    prev_count = int(recent.get(count_key, 0)) if str(recent.get(count_key, 0)).isdigit() else 0
    if isinstance(prev, str) and prev in candidates and prev_count < 2:
        recent[count_key] = prev_count + 1
        return prev
    for c in candidates:
        if c != prev:
            recent[key] = c
            recent[count_key] = 1
            return c
    chosen = candidates[0]
    recent[key] = chosen
    recent[count_key] = 1
    return chosen


PSYCHOLOGY_TRANSLATION_DICT = {
    ("太陽", "山羊座"): {
        "traits": ["考えを現実化する力", "計画思考", "責任感"],
        "behaviors": ["情報を構造化してから動く", "目標を逆算して手順化する"],
    },
    ("月", "蟹座"): {
        "traits": ["感情の機微を読む力", "保護本能", "安心基地を作る力"],
        "behaviors": ["場の空気を先に整える", "身近な人の状態を観察する"],
    },
    ("水星", "乙女座"): {
        "traits": ["分析力", "言語化能力", "改善志向"],
        "behaviors": ["曖昧な情報を整理して伝える", "小さな誤差を修正する"],
    },
}

HOUSE_LIFE_EVENT_MAP = {
    1: ["自己イメージの更新", "第一印象", "行動スタイル"],
    2: ["収入と支出", "所有", "自己価値感"],
    3: ["学習", "対話", "書く・教える"],
    4: ["家族", "居場所", "生活基盤"],
    5: ["恋愛", "創作活動", "趣味", "遊び", "自己表現"],
    6: ["仕事の運用", "健康習慣", "日課の整備"],
    7: ["パートナーシップ", "契約", "対人調整"],
    8: ["深い絆", "共有資産", "感情の再生"],
    9: ["学び直し", "旅", "信念の拡張"],
    10: ["キャリア", "社会評価", "責任ある役割"],
    11: ["仲間", "コミュニティ", "将来構想"],
    12: ["休息", "内省", "手放し"],
}


def translate_life_event(house: int) -> list[str]:
    return HOUSE_LIFE_EVENT_MAP.get(house, ["日常テーマの再調整"])


def translate_psychology(planet: str, sign: str, house: int) -> dict[str, list[str]]:
    base = PSYCHOLOGY_TRANSLATION_DICT.get((planet, sign), {
        "traits": [f"{planet}の資質を{sign}的に使う力"],
        "behaviors": [f"{planet}テーマを{sign}らしく表現する"],
    })
    return {
        "psychological_traits": base["traits"],
        "behavior_patterns": base["behaviors"],
        "life_events": translate_life_event(house),
    }


def synthesize_life_narrative(phenomenon: str, emotions: str, action_hint: str) -> str:
    return f"現象: {phenomenon}。感情: {emotions}。行動ヒント: {action_hint}。"


def generate_progressed_theme(progressed_chart: list[dict]) -> list[str]:
    themes: list[str] = []
    for p in sorted(progressed_chart, key=lambda x: float(x.get("house", 99)))[:3]:
        psych = translate_psychology(p.get("planet", ""), p.get("sign", ""), int(p.get("house", 0)))
        themes.append(
            synthesize_life_narrative(
                f"最近は{p.get('planet')}の{p.get('sign')}・第{p.get('house')}ハウス領域（{' / '.join(psych['life_events'][:2])}）が動きやすい",
                f"以前より『{' / '.join(psych['psychological_traits'][:2])}』を意識しやすい",
                f"今は{' / '.join(psych['behavior_patterns'][:2])}を小さく試すと流れに乗りやすい",
            )
        )
    return themes


def extract_transit_theme(aspect_sets: list[tuple[list[dict], str]]) -> str:
    all_aspects = [a for aspects, _ in aspect_sets for a in aspects if a.get("aspect") in MAJOR_ASPECTS]
    themes: list[str] = []
    for asp in sorted(all_aspects, key=_aspect_priority_score)[:4]:
        if "木星" in {asp.get("planet1"), asp.get("planet2")}:
            themes.append("拡大と挑戦、新機会")
        elif "土星" in {asp.get("planet1"), asp.get("planet2")}:
            themes.append("責任再編と基盤強化")
        elif "天王星" in {asp.get("planet1"), asp.get("planet2")}:
            themes.append("変化と刷新")
        else:
            themes.append("優先順位の再設定")
    return " / ".join(dict.fromkeys(themes)) if themes else "静かな調整期"


def generate_triple_synthesis(natal_chart: list[dict], progress_chart: list[dict], aspect_sets: list[tuple[list[dict], str]]) -> tuple[str, str, str]:
    natal = _natal_core_narrative(natal_chart)
    progressed = _progress_narrative(natal_chart, progress_chart)
    transit = extract_transit_theme(aspect_sets)
    why_now = f"本質（{_top_key(_element_mode_counts(natal_chart)[0])}）と最近の内面変化が重なり、外部では『{transit}』が同時進行するため、今は転換点です"
    hint = "今は『続けること1つ・減らすこと1つ・試すこと1つ』を毎週記録すると、内面変化と現実成果が接続しやすくなります"
    return natal, progressed, synthesize_life_narrative(why_now, "納得と不安が同時に出やすい", hint)


def assign_aspect_to_relationship_theme(aspects: list[dict]) -> dict[str, list[dict]]:
    assigned = {k: [] for k in SYNASTRY_SECTION_TITLES}
    used: set[tuple[frozenset[str], str]] = set()
    for asp in aspects:
        key = (frozenset([asp.get("planet1"), asp.get("planet2")]), asp.get("aspect"))
        if key in used:
            continue
        used.add(key)
        section = assign_aspect_to_section([asp])
        for k, vals in section.items():
            if vals and len(assigned[k]) < 2:
                assigned[k].extend(vals[:1])
                break
    return assigned


def choose_non_repeating_action_hint(hints: list[str], used_hints: set[str], limit: int = 1) -> list[str]:
    out = []
    for hint in hints:
        if hint in used_hints:
            continue
        used_hints.add(hint)
        out.append(hint)
        if len(out) >= limit:
            break
    if not out and hints:
        out.append(hints[0])
    return out


BARNUM_LINES_BY_PLANET = {
    "太陽": [
        "自分では普通だと思っているこだわりを、周囲は意外と才能だと見ています。",
        "迷いがあっても、最後は『自分で決めたい』気持ちがしっかり残る人です。",
    ],
    "月": [
        "平気そうに見える日でも、内側ではかなり細やかに空気を読んでいます。",
        "人に合わせられる一方で、心の奥には『ここは分かってほしい』線があります。",
    ],
    "火星": [
        "頑張れる人ですが、頑張れるからこそ限界まで我慢して気づきやすい面があります。",
    ],
    "土星": [
        "責任感が強く、頼られるほど黙って背負い込みやすいところがあるでしょう。",
    ],
}

ACTIONS_BY_PLANET = {
    "太陽": ["週1回、今いちばん力を注ぎたいテーマを30分だけ深掘りする"],
    "月": ["安心できる相手と、感情を言葉にする時間を先に予定へ入れる"],
    "水星": ["考えを3行メモにしてから会話や意思決定に入る"],
    "金星": ["心地よいと感じる環境を1つ整える（香り・音・照明など）"],
    "火星": ["1日15分の短い運動や作業で、行動エネルギーを安全に放出する"],
    "木星": ["学びは『広く』より『1テーマを4週間続ける』で運用する"],
    "土星": ["重い課題は25分単位で区切り、終わりを先に決めて取り組む"],
}

ACTIONS_BY_ASPECT_TYPE = {
    "トライン": "得意な流れを仕事や対人で意識的に再現する",
    "セクスタイル": "チャンスが来たら小さく即応し、機会損失を減らす",
    "コンジャンクション": "強みが集中する領域を1つに絞って深く育てる",
    "スクエア": "摩擦を感じる場面を記録し、事前ルールを決めて再発を防ぐ",
    "オポジション": "二者択一にせず、週単位で配分を決めて両立を試す",
    "クインカンクス（150°）": "合わなさを責めず、手順や時間帯を調整して運用する",
}

ACTIONS_BY_BALANCE = {
    ("地", "固定"): ["毎日同じ型で積み上げる作業を主軸にする", "月2回は場所や手順を変えて硬直を防ぐ"],
    ("火", "活動"): ["朝に最重要タスクを先に着手する", "勢い任せを防ぐため締切を細かく区切る"],
    ("風", "柔軟"): ["情報収集は時間上限を決める", "学んだ内容を当日中に1回アウトプットする"],
}


def generate_barnum_line(p: dict) -> str:
    lines = BARNUM_LINES_BY_PLANET.get(p.get("planet"), [])
    if not lines:
        return ""
    idx = (p.get("house", 1) + len(p.get("sign", ""))) % len(lines)
    return lines[idx]


def suggest_actions_for_placement(p: dict, used_hints: set[str] | None = None, limit: int = 2) -> list[str]:
    actions = []
    actions.extend(ACTIONS_BY_PLANET.get(p.get("planet"), []))
    house = p.get("house")
    if house == 7:
        actions.append("一対一の関係では、期待を察してもらう前に先に言葉で共有する")
    elif house == 9:
        actions.append("興味のある思想・分野を1つ決め、表面的な情報より継続研究を優先する")
    elif house == 12:
        actions.append("予定表に『何もしない回復時間』を先に確保して消耗を防ぐ")
    deduped = []
    for a in actions:
        if a not in deduped:
            deduped.append(a)
    if used_hints is None:
        return deduped[:limit]
    return choose_non_repeating_action_hint(deduped, used_hints, limit=limit)


def suggest_actions_for_aspect(asp: dict, used_hints: set[str] | None = None, limit: int = 1) -> list[str]:
    action = ACTIONS_BY_ASPECT_TYPE.get(asp.get("aspect"))
    if not action:
        return []
    if used_hints is None:
        return [action][:limit]
    return choose_non_repeating_action_hint([action], used_hints, limit=limit)


def suggest_actions_for_balance(chart: list[dict], limit: int = 2) -> list[str]:
    major = [p for p in chart if p.get("planet") in MAIN_INTERPRET_PLANETS]
    element_count = {"火": 0, "地": 0, "風": 0, "水": 0}
    mode_count = {"活動": 0, "固定": 0, "柔軟": 0}
    for p in major:
        meta = _SIGN_META.get(p.get("sign"), {})
        e = meta.get("element")
        m = meta.get("mode")
        if e in element_count:
            element_count[e] += 1
        if m in mode_count:
            mode_count[m] += 1
    key = (max(element_count, key=element_count.get), max(mode_count, key=mode_count.get))
    return ACTIONS_BY_BALANCE.get(key, ["得意パターンを固定しつつ、月1回は新しい方法を試して更新する"])[:limit]


def _element_mode_counts(chart: list[dict]) -> tuple[dict[str, int], dict[str, int]]:
    major = [p for p in normalize_node_objects(chart) if p.get("planet") in MAIN_INTERPRET_PLANETS]
    element_count = {"火": 0, "地": 0, "風": 0, "水": 0}
    mode_count = {"活動": 0, "固定": 0, "柔軟": 0}
    for p in major:
        sign_meta = _SIGN_META.get(p.get("sign"), {})
        element = sign_meta.get("element")
        mode = sign_meta.get("mode")
        if element in element_count:
            element_count[element] += 1
        if mode in mode_count:
            mode_count[mode] += 1
    return element_count, mode_count


def _top_key(counts: dict[str, int]) -> str:
    return max(counts, key=counts.get)


def _natal_core_narrative(natal_chart: list[dict]) -> str:
    element_count, mode_count = _element_mode_counts(natal_chart)
    top_element = _top_key(element_count)
    top_mode = _top_key(mode_count)

    element_map = {
        "火": "人格は『まず動いて世界を切り開く』ことで輪郭がはっきりします。熱量が高いぶん、短距離での立ち上がりが速いタイプです",
        "地": "人格は『現実に落とし込んで積み上げる』ことで安定します。結果を作るための手順設計が得意なタイプです",
        "風": "人格は『情報をつないで意味を見出す』ことで活性化します。思考の回転が速く、選択肢を増やして最適化するタイプです",
        "水": "人格は『感情の質を整える』ことで本来の力が出ます。空気や関係性の機微を読み、深い共感で動くタイプです",
    }
    mode_map = {
        "活動": "行動傾向は、完璧を待つより先に着手して流れを作るほうが噛み合います",
        "固定": "行動傾向は、いったん決めた方針を深く育てるほど成果が太くなります",
        "柔軟": "行動傾向は、状況を見ながら方法を微調整すると実力が伸びます",
    }
    think_map = {
        "火": "思考スタイルは『直感先行→検証で磨く』型になりやすいです",
        "地": "思考スタイルは『事実確認→実行可能性を評価』型になりやすいです",
        "風": "思考スタイルは『比較検討→言語化で整理』型になりやすいです",
        "水": "思考スタイルは『感覚把握→納得感で決断』型になりやすいです",
    }

    return f"{element_map[top_element]}。{think_map[top_element]}。{mode_map[top_mode]}。"


def _progress_narrative(natal_chart: list[dict], progress_chart: list[dict]) -> str:
    natal_elements, natal_modes = _element_mode_counts(natal_chart)
    progress_elements, progress_modes = _element_mode_counts(progress_chart)
    natal_top_element = _top_key(natal_elements)
    progress_top_element = _top_key(progress_elements)
    natal_top_mode = _top_key(natal_modes)
    progress_top_mode = _top_key(progress_modes)

    shift_lines = []
    if natal_top_element != progress_top_element:
        shift_lines.append(
            f"ここ数年は、これまでの『{natal_top_element}的な進め方』から『{progress_top_element}的な進め方』へ重心が移り、"
            "同じ目標でも取り組み方を変えたくなる感覚が強まりやすい時期です"
        )
    else:
        shift_lines.append(
            f"ここ数年は『{progress_top_element}』の資質を深掘りする流れが続き、"
            "以前よりも「自分らしい基準で選ぶ」感覚が明確になりやすい時期です"
        )

    if natal_top_mode != progress_top_mode:
        shift_lines.append(
            f"行動リズムも『{natal_top_mode}』から『{progress_top_mode}』へ変化し、"
            "昔は平気だった進め方に違和感が出るのは自然な反応です"
        )

    shift_lines.append("最近『このままではしっくりこない』と感じているなら、その感覚は内面の成熟サインです")
    return "。".join(shift_lines) + "。"


def _extract_transit_theme(aspect_sets: list[tuple[list[dict], str]]) -> str:
    all_aspects = [a for aspects, _ in aspect_sets for a in aspects]
    transit_aspects = [a for a in all_aspects if "トランジット" in str(a.get("category", ""))]
    if not transit_aspects:
        transit_aspects = all_aspects

    hard = {"スクエア", "オポジション", "クインカンクス（150°）"}
    soft = {"トライン", "セクスタイル", "コンジャンクション"}
    hard_count = sum(1 for a in transit_aspects if a.get("aspect") in hard)
    soft_count = sum(1 for a in transit_aspects if a.get("aspect") in soft)

    if hard_count > soft_count:
        return (
            "今は外部環境からの要請が強まり、優先順位の再設定を迫られやすい時期です。"
            "負荷はかかりますが、不要な約束や惰性の習慣を手放すほど身軽さを取り戻せます"
        )
    if soft_count > hard_count:
        return (
            "今は追い風を受け取りやすく、協力・学習・発信が成果につながりやすい時期です。"
            "小さな挑戦を公開し、反応の良いものへ資源を寄せるほど流れに乗れます"
        )
    return (
        "今は追い風と負荷が同時に来る混合フェーズです。"
        "守る領域と広げる領域を分けて運用すると、消耗を抑えながら前進しやすくなります"
    )


def _triple_integration_narrative(natal_chart: list[dict], progress_chart: list[dict], aspect_sets: list[tuple[list[dict], str]]) -> tuple[str, str]:
    natal_top_element = _top_key(_element_mode_counts(natal_chart)[0])
    progress_top_element = _top_key(_element_mode_counts(progress_chart)[0])
    transit_theme = _extract_transit_theme(aspect_sets)

    integration = (
        f"今この時期が意味を持つのは、あなたの本質である『{natal_top_element}』の使い方を、"
        f"現在の内面テーマ『{progress_top_element}』に合わせて再編集する転換点だからです。"
        f"{transit_theme}。"
        "過去の成功法則をそのまま繰り返すより、目的は据え置きで手段を更新したほうが、運と実力の接続が強まります"
    )

    actions = (
        "活かし方は3つです。①毎週1回、予定を『続ける・減らす・試す』の3分類で棚卸しする。"
        "②意思決定は10分で一次判断し、24時間以内に最小実験へ落とす。"
        "③感情が乱れた日は成果目標を下げ、行動目標（連絡1件・メモ10行など）だけ達成して自己効力感を維持する"
    )
    return integration + "。", actions + "。"


def synthesize_planet_sign_house(
    p: dict,
    suppress_sign_detail: bool = False,
    recent_templates: dict[str, str] | None = None,
) -> str:
    """Planet × Sign × House を統合文として生成する。"""
    planet = p.get("planet", "")
    sign = p.get("sign", "")
    house = p.get("house", 0)
    ps = synthesize_planet_sign(p, suppress_redundant=suppress_sign_detail)
    ph = synthesize_planet_house(p, recent_templates=recent_templates).rstrip("。")
    motion_candidates = [
        "内面で熟成してから形にする流れを取りやすいです" if p.get("retrograde") else "行動を重ねながら答えを磨きやすいです",
        "慎重に組み立てるほど安定感が増します" if p.get("retrograde") else "まず着手してから調整するほど精度が上がります",
    ]
    ending = ENDING_VARIATIONS[house % len(ENDING_VARIATIONS)]
    motion = motion_candidates[house % len(motion_candidates)]
    return f"{planet}が{sign}の第{house}ハウス。{ps}。{ph}。{motion}。{ending}"


def dedupe_similar_lines(lines: list[str]) -> list[str]:
    seen = set()
    out = []
    for line in lines:
        key = line.replace("。", "").replace("、", "")[:40]
        if key not in seen:
            seen.add(key)
            out.append(line)
    return out


def synthesize_aspect(asp: dict, used_hints: set[str] | None = None, mode: str = "natal") -> str:
    """Planet1 × Aspect × Planet2 の意味合成。"""
    enriched = interpret_aspect(asp, mode=mode)
    action = suggest_actions_for_aspect(asp, used_hints=used_hints)
    guidance = action[0] if action else enriched["practical_guidance"]
    life_events = " / ".join(enriched["life_events"])

    return (
        f"{enriched['identity']}。"
        f"{enriched['opener']}{enriched['psychological_dynamic']}。"
        f"生活現象: {enriched['life_manifestation']}。"
        f"強度と時期: {enriched['timing_or_intensity']}。"
        f"サイン連動: {enriched['sign_interaction']}。"
        f"ハウス連動: {enriched['house_interaction']}。"
        f"起こりやすい場面: {life_events}。"
        f"実践ガイド: {guidance}。"
    )


def interpret_planet_position(placement: dict) -> dict[str, str]:
    """単一配置をUIやAPIで再利用しやすい4層構造へ整形する。"""
    psych = translate_psychology(
        placement.get("planet", ""),
        placement.get("sign", ""),
        int(placement.get("house", 0) or 0),
    )
    actions = suggest_actions_for_placement(placement, limit=2)
    placement_summary = synthesize_planet_sign_house(placement)
    return {
        "title": f"{placement.get('planet', '')} in {placement.get('sign', '')} house {placement.get('house', '')}",
        "placement_meaning": placement_summary,
        "psychological_pattern": " / ".join(psych["psychological_traits"][:3]),
        "life_manifestation": " / ".join(psych["life_events"][:3]),
        "practical_advice": " / ".join(actions) if actions else "日々の反応を観察し、再現しやすい行動パターンを残してください。",
    }


def interpret_house_overlay(base_chart: list[dict], overlay_chart: list[dict], base_cusps: list[float] | None = None) -> list[dict[str, str]]:
    """相手天体がベースチャートのどのハウスに入るかを簡潔に解釈する。"""
    if not base_cusps:
        return []
    overlay_lines = _syn_house_overlay(base_chart, base_cusps, overlay_chart)
    results: list[dict[str, str]] = []
    for line in overlay_lines:
        body = line.lstrip("- ").strip()
        results.append({
            "title": "House Overlay",
            "placement_meaning": body,
            "psychological_pattern": "関係の中で反応しやすい領域が強調されます。",
            "life_manifestation": "同居感覚、対人期待、深い結びつき、社会的目標に影響しやすい配置です。",
            "practical_advice": "強く反応するテーマほど、期待を言語化して境界線を先に共有してください。",
        })
    return results


def synthesize_interpretation(
    placements: list[dict[str, str]],
    aspects: list[dict[str, str]],
    overlays: list[dict[str, str]] | None = None,
    mode: str = "natal",
) -> str:
    """配置・アスペクト・オーバーレイを一つの可読レポートに統合する。"""
    mode_label = CHART_TYPE_LABELS.get(mode, mode)
    summary_label = STRUCTURED_SUMMARY_LABELS.get(mode, f"{mode_label}の要点サマリー")
    guidance = STRUCTURED_SUMMARY_GUIDANCE.get(mode, "詳細レポートを読む前に、重要ポイントだけ先に把握するための整理版です。")
    lines = [
        f"【{summary_label}】",
        f"対象モード: {mode_label}",
        f"使いどころ: {guidance}",
        "位置づけ: 『詳細レポート』が文章でじっくり読む版で、こちらは要点だけを素早く確認する版です。",
        "=" * 60,
    ]
    if placements:
        lines.append("\n【主要な配置】")
        for item in placements[:5]:
            lines.append(f"- {item['placement_meaning']}")
            lines.append(f"  心理傾向: {item['psychological_pattern']}")
            lines.append(f"  出やすい形: {item['life_manifestation']}")
            lines.append(f"  活かし方: {item['practical_advice']}")
    if aspects:
        lines.append("\n【主要なアスペクト】")
        for item in aspects[:5]:
            lines.append(f"- {item['identity']}")
            lines.append(f"  心理テーマ: {item['psychological_dynamic']}")
            lines.append(f"  出やすい形: {item['life_manifestation']}")
            lines.append(f"  実践ヒント: {item['practical_guidance']}")
    if overlays:
        lines.append("\n【関係の重なり方】")
        for item in overlays[:4]:
            lines.append(f"- {item['placement_meaning']}")
            lines.append(f"  実践ヒント: {item['practical_advice']}")
    lines.extend(
        [
            "\n【この要点サマリーの読み方】",
            "- まず『対象モード』と『主要な配置』で土台を確認します。",
            "- 次に『主要なアスペクト』で、今強く動きやすいテーマを拾います。",
            "- 迷ったときは、詳細レポートに戻って背景説明を読み足す使い方がおすすめです。",
        ]
    )
    return "\n".join(lines)


def build_compact_interpretation_payload(
    *,
    placements: list[dict[str, str]],
    aspects: list[dict[str, str]],
    overlays: list[dict[str, str]] | None = None,
    mode: str = "natal",
    subject_label: str = "あなた",
) -> dict[str, object]:
    mode_label = CHART_TYPE_LABELS.get(mode, mode)
    payload: dict[str, object] = {
        "対象モード": mode_label,
        "サマリー種別": STRUCTURED_SUMMARY_LABELS.get(mode, f"{mode_label}の要点サマリー"),
        "対象者": subject_label,
        "要約目的": STRUCTURED_SUMMARY_GUIDANCE.get(mode, "重要ポイントだけを短時間で把握するための圧縮データです。"),
        "主要な配置": [
            {
                "配置": item["placement_meaning"],
                "心理傾向": item["psychological_pattern"],
                "出やすい形": item["life_manifestation"],
                "活かし方": item["practical_advice"],
            }
            for item in placements[:4]
        ],
        "主要なアスペクト": [
            {
                "アスペクト": item["identity"],
                "心理テーマ": item["psychological_dynamic"],
                "出やすい形": item["life_manifestation"],
                "実践ヒント": item["practical_guidance"],
            }
            for item in aspects[:4]
        ],
    }
    if overlays:
        payload["関係の重なり方"] = [
            {
                "重なり": item["placement_meaning"],
                "実践ヒント": item["practical_advice"],
            }
            for item in overlays[:3]
        ]
    return payload


def build_llm_reading_prompt(compact_payload: dict[str, object], *, mode: str = "natal") -> str:
    compact_json = json.dumps(compact_payload, ensure_ascii=False, indent=2)
    intent = LLM_READING_INTENTS.get(mode, "圧縮データから重要な読みどころを整理する")
    return "\n".join(
        [
            "あなたは占星術の要点整理を手伝う補助役です。",
            f"今回の目的: {intent}。",
            "以下の圧縮データだけを根拠に、日本語で読み解いてください。",
            "守ること:",
            "- データに無いことを断定しない",
            "- まず全体像を短くまとめる",
            "- 次に強み / 課題 / 実践ヒント を見出し付きで整理する",
            "- 専門用語は必要な場合のみ短く説明する",
            "- 出力は日本語のみで、英語見出しは使わない",
            "",
            "圧縮データ:",
            compact_json,
        ]
    )



def _aspect_priority_score(asp: dict) -> tuple:
    majors = {"太陽", "月", "水星", "金星", "火星", "木星", "土星"}
    p1, p2 = asp.get("planet1"), asp.get("planet2")
    major_count = int(p1 in majors) + int(p2 in majors)
    orb = float(asp.get("orb", 99.0))
    rarity_bonus = 0
    if p1 in {"トゥルーノード", "ドラゴンヘッド", "ノード軸ヘッド"} or p2 in {"トゥルーノード", "ドラゴンヘッド", "ノード軸ヘッド"}:
        rarity_bonus -= 1
    return (-major_count, orb, rarity_bonus)


def generate_report_header(
    chart_mode: str,
    person_name: str = "あなた",
    target_datetime: str | None = None,
    target_location: str | None = None,
    person2_name: str | None = None,
    target_datetime2: str | None = None,
    target_location2: str | None = None,
) -> list[str]:
    label = CHART_TYPE_LABELS.get(chart_mode, chart_mode)
    lines = [
        f"＊ {person_name}の星読みレポート ＊" if chart_mode != "synastry" else f"＊ {person_name} × {person2_name or '相手'} 相性レポート ＊",
        f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"チャート種別: {label}",
    ]
    if target_datetime:
        lines.append(f"対象日時: {target_datetime}")
    if target_location:
        lines.append(f"対象地点: {target_location}")
    if chart_mode == "synastry":
        if target_datetime2:
            lines.append(f"相手の対象日時: {target_datetime2}")
        if target_location2:
            lines.append(f"相手の対象地点: {target_location2}")
    if chart_mode == "triple":
        lines.append("統合対象: ネイタル（核）＋プログレス（内面変化）＋トランジット（外的時期性）")
    lines.append("=" * 60)
    return lines


REPORT_READING_NOTES = {
    "natal": [
        "出生図は『変わらない運命』の断定ではなく、強みと偏りの扱い方を確認する地図として使うと実務的です。",
        "当たり外れより、『どの行動を増やすと安定しやすいか』に重心を置いて読むほど活かしやすくなります。",
    ],
    "progressed": [
        "プログレスは出来事の断定より、内面の重心がどちらへ移っているかを読むと精度が安定します。",
        "違和感の出た習慣を責めるより、『今の自分に合う運用へ更新するサイン』として扱うと使いやすいです。",
    ],
    "transit": [
        "トランジットは外部刺激の強弱を見るレポートなので、単発の吉凶より時期の使い方に注目すると実務向きです。",
        "強いヒットがある時ほど、反応の良かった行動を短い周期で記録すると波を味方にしやすくなります。",
    ],
    "triple": [
        "トリプルは『本質・内面変化・外部時期』を同時に読む統合ビューなので、全部を一度に変えるより優先順位を決めるのがコツです。",
        "転換点に見える時ほど、続けることと減らすことを分けて記録すると判断の質が安定します。",
    ],
    "synastry": [
        "相性レポートは相手の人格を断定するためではなく、二人の運用で摩耗しやすい点と伸びやすい点を把握する材料です。",
        "良し悪しの判定より、安心を増やす手順と衝突後の回復導線を見つける読み方が実務的です。",
    ],
}


def _is_report_separator(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and set(stripped) == {"="}


def _normalize_report_bullet(line: str) -> str | None:
    text = str(line or "").strip()
    if not text:
        return None
    if text.startswith("- "):
        return text
    if text.startswith("-"):
        return f"- {text[1:].strip()}"
    return f"- {text}"


def _build_report_section(title: str, items: list[str]) -> list[str]:
    normalized: list[str] = []
    for item in items:
        bullet = _normalize_report_bullet(item)
        if bullet:
            normalized.append(bullet)
    deduped = dedupe_similar_lines(normalized)
    if not deduped:
        return []
    return ["", title, *deduped]


def _apply_report_quality_frame(
    report_text: str,
    *,
    mode: str,
    summary_lines: list[str] | None = None,
    action_lines: list[str] | None = None,
    note_lines: list[str] | None = None,
) -> str:
    if "【最初に押さえたい要点】" in report_text and "【実践ガイド】" in report_text and "【読み方メモ】" in report_text:
        return report_text

    lines = report_text.splitlines()
    summary_block = _build_report_section("【最初に押さえたい要点】", summary_lines or [])
    action_block = _build_report_section("【実践ガイド】", action_lines or [])
    note_block = _build_report_section("【読み方メモ】", [*(note_lines or []), *REPORT_READING_NOTES.get(mode, [])])

    if summary_block:
        first_separator = next((idx for idx, line in enumerate(lines) if _is_report_separator(line)), None)
        insert_at = first_separator + 1 if first_separator is not None else 0
        lines[insert_at:insert_at] = summary_block

    trailing_blocks: list[str] = []
    for block in (action_block, note_block):
        if block:
            trailing_blocks.extend(block)
    if trailing_blocks:
        separator_indices = [idx for idx, line in enumerate(lines) if _is_report_separator(line)]
        insert_at = separator_indices[-1] if separator_indices else len(lines)
        lines[insert_at:insert_at] = trailing_blocks
    return "\n".join(lines)


def _placement_focus_line(label: str, placement: dict | None) -> str | None:
    if not placement:
        return None
    sign = str(placement.get("sign", ""))
    sign_label = sign if sign.endswith("座") else f"{sign}座"
    psych = translate_psychology(
        placement.get("planet", ""),
        placement.get("sign", ""),
        int(placement.get("house", 0) or 0),
    )
    traits = " / ".join(psych["psychological_traits"][:2]) or "その天体テーマ"
    return (
        f"{label}: {placement.get('planet')}が{sign_label}・第{placement.get('house')}ハウスにあり、"
        f"『{traits}』が前面に出やすい配置です。"
    )


def _first_placement_action(placement: dict | None) -> str | None:
    if not placement:
        return None
    actions = suggest_actions_for_placement(placement, limit=1)
    return actions[0] if actions else None


def _aspect_focus_line(label: str, asp: dict | None, mode: str) -> str | None:
    if not asp:
        return None
    enriched = interpret_aspect(asp, mode=mode)
    return (
        f"{label}: {asp.get('planet1')}と{asp.get('planet2')}の{asp.get('aspect')}が"
        f"『{enriched['psychological_dynamic']}』を動かしやすい局面です。"
    )


def _first_aspect_action(asp: dict | None, mode: str) -> str | None:
    if not asp:
        return None
    actions = suggest_actions_for_aspect(asp, limit=1)
    if actions:
        return actions[0]
    return interpret_aspect(asp, mode=mode)["practical_guidance"]


def _build_natal_style_interpretation(
    natal_chart: list,
    aspects_sets: list,
    composite_sets: list,
    person_name: str = "あなた",
    header_lines: list[str] | None = None,
    mode: str = "natal",
) -> str:
    chart = normalize_node_objects(natal_chart)
    recent_templates: dict[str, str] = {}
    used_hints: set[str] = set()
    lines = header_lines[:] if header_lines else [
        f"＊ {person_name}の星読みレポート ＊",
        f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
    ]
    lines.append("\n【核 / 人生テーマ】")

    sun = next((p for p in chart if p.get("planet") == "太陽"), None)
    moon = next((p for p in chart if p.get("planet") == "月"), None)
    asc = next((p for p in chart if p.get("planet") == "アセンダント"), None)
    seen_signs: set[str] = set()

    if sun:
        lines.append(f"- {synthesize_planet_sign_house(sun, recent_templates=recent_templates)}")
        lines.append(f"  {generate_barnum_line(sun)}")
        lines.append(f"  {choose_non_repeating_template(ACTION_HINT_VARIATIONS, 'action_hint', recent_templates).format(hint=' / '.join(suggest_actions_for_placement(sun, used_hints=used_hints)))}")
        seen_signs.add(sun.get("sign"))
    if moon:
        lines.append(f"- {synthesize_planet_sign_house(moon, suppress_sign_detail=moon.get('sign') in seen_signs, recent_templates=recent_templates)}")
        lines.append(f"  {generate_barnum_line(moon)}")
        lines.append(f"  {choose_non_repeating_template(ACTION_HINT_VARIATIONS, 'action_hint', recent_templates).format(hint=' / '.join(suggest_actions_for_placement(moon, used_hints=used_hints)))}")
        seen_signs.add(moon.get("sign"))
    if asc:
        lines.append(f"- 社会への見え方: {synthesize_planet_sign_house(asc, suppress_sign_detail=asc.get('sign') in seen_signs, recent_templates=recent_templates)}")

    lines.append(f"- 全体バランス: {summarize_element_mode_balance(chart)}")
    lines.append(f"  {choose_non_repeating_template(ACTION_HINT_VARIATIONS, 'action_hint', recent_templates).format(hint=' / '.join(choose_non_repeating_action_hint(suggest_actions_for_balance(chart), used_hints, limit=2)))}")

    lines.append("\n【資質（感情と対人傾向）】")
    for pname in ["月", "金星", "火星"]:
        p = next((obj for obj in chart if obj.get("planet") == pname), None)
        if p:
            lines.append(f"- {synthesize_planet_sign_house(p, suppress_sign_detail=p.get('sign') in seen_signs, recent_templates=recent_templates)}")
            barnum = generate_barnum_line(p)
            if barnum:
                lines.append(f"  {barnum}")
            lines.append(f"  {choose_non_repeating_template(ACTION_HINT_VARIATIONS, 'action_hint', recent_templates).format(hint=' / '.join(suggest_actions_for_placement(p, used_hints=used_hints, limit=1)))}")
            seen_signs.add(p.get("sign"))

    major_aspects = []
    for aspects, _title in aspects_sets:
        major_aspects.extend([a for a in aspects if a.get("aspect") in ASPECT_MEANING])
    major_aspects = sorted(dedupe_aspects(major_aspects), key=_aspect_priority_score)

    lines.append("\n【才能の流れ（自然に伸びる資質）】")
    talent_lines = []
    for asp in major_aspects:
        if asp.get("aspect") in {"トライン", "セクスタイル", "コンジャンクション"}:
            talent_lines.append(f"- {synthesize_aspect(asp, used_hints=used_hints, mode=mode)}")
        if len(talent_lines) >= 4:
            break
    lines.extend(dedupe_similar_lines(talent_lines) or ["- 才能は『やってみる→調整する』の反復で自然に育ちます。"])

    lines.append("\n【課題（葛藤しやすいテーマ）】")
    challenge_lines = []
    for asp in major_aspects:
        if asp.get("aspect") in {"スクエア", "オポジション", "クインカンクス（150°）"}:
            challenge_lines.append(f"- {synthesize_aspect(asp, used_hints=used_hints, mode=mode)}")
        if len(challenge_lines) >= 4:
            break
    lines.extend(dedupe_similar_lines(challenge_lines) or ["- 大きな葛藤は少なめ。だからこそ、自分から課題設定すると成長が早まります。"])

    lines.append("\n【特別な複合配置】")
    any_composite = False
    deduped_composites = []
    for composites, _title in composite_sets:
        deduped_composites.extend(dedupe_composite_patterns(composites))
    for comp in dedupe_composite_patterns(deduped_composites):
        tmpl = _COMPOSITE_INTERP.get(comp.get("type"))
        if tmpl:
            planets = "・".join(comp.get("planets", []))
            lines.append(f"- {tmpl.format(planets=planets)}")
            any_composite = True
    if not any_composite:
        lines.append("- 今回は主要な複合配置は検出されませんでした。")

    lines.append("\n【統合ポイント / 総括】")
    lines.append("- 強みは『深く考える力』と『続ける力』。この2つを同じテーマに集めるほど、結果が伸びます。")
    lines.append("- 無理を重ねる前に、感情のメンテナンス時間を予定化すると運が安定します。")
    lines.append("- 迷ったら、得意な型に戻る→小さく試す→記録する、この3手で流れを立て直せます。")

    lines.append("\n" + "=" * 60)
    lines.append("※このレポートは天体配置に基づく自動生成テキストです。")
    return "\n".join(lines)


SYN_PRIORITY_PAIRS = [
    frozenset(["太陽", "月"]),
    frozenset(["金星", "火星"]),
    frozenset(["月", "土星"]),
    frozenset(["月", "冥王星"]),
    frozenset(["月", "天王星"]),
    frozenset(["水星", "月"]),
    frozenset(["金星", "土星"]),
    frozenset(["太陽", "土星"]),
    frozenset(["太陽", "金星"]),
    frozenset(["火星", "土星"]),
    frozenset(["月", "金星"]),
    frozenset(["水星", "金星"]),
    frozenset(["水星", "火星"]),
]

SYNASTRY_SECTION_TITLES = {
    "attraction_reason": "【1. 二人が惹かれやすい理由】",
    "emotional": "【2. 感情面で起こりやすいこと】",
    "romance": "【3. 恋愛・距離感・attraction】",
    "friction": "【4. すれ違いやすい点】",
    "stability": "【5. 長続きの鍵】",
    "growth": "【6. この関係が育てるテーマ】",
}

MAJOR_RELATIONSHIP_ASPECTS = {"コンジャンクション", "オポジション", "トライン", "スクエア", "セクスタイル"}
DEEMPHASIZED_MINOR_ASPECTS = {
    "ノヴァイル（40°）", "セプタイル（51.43°）", "トライセプタイル（154.29°）", "バイクインタイル（144°）",
}

SECTION_TEMPLATE_PATTERNS = {
    "attraction_reason": [["aspect", "emotion"], ["emotion", "aspect"], ["aspect"], ["hint_only"]],
    "emotional": [["emotion", "aspect", "hint"], ["aspect", "emotion"], ["emotion", "hint"], ["aspect"]],
    "romance": [["aspect", "emotion", "hint"], ["emotion", "aspect"], ["hint_only"], ["aspect"]],
    "friction": [["aspect", "warning", "hint"], ["warning", "hint"], ["aspect", "hint"], ["hint_only"]],
    "stability": [["aspect", "hint"], ["hint", "aspect"], ["hint_only"], ["aspect", "emotion"]],
    "growth": [["emotion", "aspect"], ["aspect", "emotion", "hint"], ["emotion"], ["hint_only"]],
}

SYNASTRY_BARNUM_LINES = {
    "attraction_reason": [
        "最初は軽い雑談でも、後からじわっと印象が残るタイプの引力が働きやすいでしょう。",
        "相手の反応速度や雰囲気に、無意識で意識が向きやすい組み合わせです。",
    ],
    "emotional": [
        "安心できる日は一気に距離が縮まり、疲れている日は沈黙が重く感じやすい波が出やすいでしょう。",
        "『わかってほしい』が強いほど、言葉の少なさが不安に変換されやすい関係です。",
    ],
    "romance": [
        "惹かれ方ははっきり出やすく、温度が合う日は一気に親密さが進みやすいでしょう。",
        "ときめきの起点が似ている反面、ペース差はそのまま距離感の差に見えやすい配置です。",
    ],
    "friction": [
        "正しさを急ぐとぶつかりやすく、意図の説明を先にすると誤解を減らしやすいでしょう。",
        "どちらも真剣だからこそ、言葉の角度ひとつで受け取り方が大きく変わりやすい関係です。",
    ],
    "stability": [
        "気分より運用を整えたときに、安心感が目に見えて増えていくタイプです。",
        "小さな約束を守る回数が、そのまま信頼残高に直結しやすいでしょう。",
    ],
    "growth": [
        "価値観の違いを処理するたびに、二人の対話力そのものが育ちやすい関係です。",
        "恋愛の枠を超えて、意思決定の質まで磨かれやすい学習テーマがあります。",
    ],
}

ACTION_HINTS_BY_THEME = {
    "attraction": [
        "初期3週間だけ『返信ペースの目安』を決め、期待値ギャップを先に減らしましょう。",
        "会う頻度は回数よりリズムを固定し、次回予定をその場で1つだけ仮置きしましょう。",
    ],
    "emotional_safety": [
        "不安になった時は『事実・気持ち・お願い』の3点を1分で伝えると受け取り違いが減ります。",
        "疲労が強い日は深い話を保留し、24時間以内の再開時間だけ先に決めましょう。",
    ],
    "conflict_repair": [
        "衝突時は結論より先に『何が痛かったか』を一文で共有し、反論は3分後に回しましょう。",
        "論点が増えたら1テーマ15分に区切り、終了時に次回の続き方を固定しましょう。",
    ],
    "long_term_stability": [
        "週1回10分で『予定・連絡・お金』を確認し、曖昧コストを先に削減しましょう。",
        "機嫌ではなくルールで運用するため、連絡の締切時刻を二人で1つだけ決めましょう。",
    ],
    "growth": [
        "価値観が割れた話題ほど、結論前に『育った環境の違い』を互いに2分ずつ話してみましょう。",
        "月末に一度『うまくいった連携』を棚卸しし、再現できる行動だけ次月へ残しましょう。",
    ],
}

ASPECT_HINTS_BY_PAIR = {
    frozenset(["月", "土星"]): {
        "emotional_safety": ["安心したい日は、約束を小さく固定して守ると月土星の信頼感が育ちます。"],
        "long_term_stability": ["真面目さが重さに変わる前に、週1回だけ『雑談だけの時間』を予定化しましょう。"],
    },
    frozenset(["金星", "火星"]): {
        "attraction": ["会う頻度とスキンシップの希望を先に言葉にすると、金星火星の温度差が魅力として機能します。"],
    },
    frozenset(["太陽", "土星"]): {
        "conflict_repair": ["指摘は『改善点1つ＋評価1つ』で伝えると、太陽土星の萎縮を防ぎやすくなります。"],
    },
    frozenset(["月", "冥王星"]): {
        "emotional_safety": ["不安が増幅した日は沈黙を放置せず、『今は不安寄り』と短く共有して依存ループを断ちましょう。"],
    },
    frozenset(["水星", "火星"]): {
        "conflict_repair": ["話し合いは『結論を急がない10分』を先に取り、言い方の速度を合わせてから本題に入りましょう。"],
    },
}

THEME_BY_SECTION = {
    "attraction_reason": "attraction",
    "emotional": "emotional_safety",
    "romance": "attraction",
    "friction": "conflict_repair",
    "stability": "long_term_stability",
    "growth": "growth",
}

SECTION_SUMMARY_LINES = {
    "attraction_reason": [
        "この関係は『気づいたら気になる』を積み上げる型で、派手さより接触リズムの設計が効きます。",
        "惹かれ方の初速は十分あるので、期待値を先に合わせるほど自然体の魅力が残りやすいでしょう。",
    ],
    "emotional": [
        "安心は自動ではなく、言葉と反応の積み重ねで育つタイプです。",
        "本音を急がず安全に出せる場を作るほど、感情の揺れは強みに転換しやすくなります。",
    ],
    "romance": [
        "恋愛温度は高まりやすい一方で、ペース差の調整が満足度を左右します。",
        "ときめきと安心の両立には、会う頻度・距離の詰め方を早めに言語化するのが近道です。",
    ],
    "friction": [
        "すれ違いは相性の悪さより、処理手順の不一致で起きやすい配置です。",
        "ぶつかった後の回復導線を先に作ると、衝突が関係の質を上げる材料に変わります。",
    ],
    "stability": [
        "長続きの鍵は感情の強さより、運用の再現性にあります。",
        "小さな合意を守る回数が増えるほど、将来不安は目に見えて軽くなるでしょう。",
    ],
    "growth": [
        "この関係は、違いを扱う技術を二人に育てる学習装置になりやすいです。",
        "相手の背景理解を深めるほど、恋愛以外の場面でも意思決定の質が上がります。",
    ],
}

PAIR_SECTION_PRIORITY = {
    frozenset(["太陽", "月"]): ["attraction_reason", "emotional"],
    frozenset(["金星", "火星"]): ["romance", "attraction_reason"],
    frozenset(["月", "土星"]): ["emotional", "stability"],
    frozenset(["太陽", "土星"]): ["friction", "stability"],
    frozenset(["月", "冥王星"]): ["emotional", "friction"],
    frozenset(["水星", "火星"]): ["friction", "growth"],
    frozenset(["金星", "土星"]): ["stability", "romance"],
    frozenset(["月", "天王星"]): ["emotional", "romance"],
    frozenset(["水星", "月"]): ["emotional", "attraction_reason"],
    frozenset(["太陽", "金星"]): ["romance", "attraction_reason"],
    frozenset(["火星", "土星"]): ["friction", "stability"],
    frozenset(["月", "金星"]): ["romance", "emotional"],
    frozenset(["水星", "金星"]): ["attraction_reason", "romance"],
}


def is_major_relationship_aspect(aspect_name: str) -> bool:
    return aspect_name in MAJOR_RELATIONSHIP_ASPECTS


def should_show_minor_aspect(asp: dict, detailed_mode: bool = False) -> bool:
    aspect = asp.get("aspect", "")
    if is_major_relationship_aspect(aspect):
        return True
    if detailed_mode:
        return True
    return aspect not in DEEMPHASIZED_MINOR_ASPECTS


def classify_synastry_aspect_theme(asp: dict) -> str:
    pair = frozenset([asp.get("planet1"), asp.get("planet2")])
    if pair in {frozenset(["金星", "火星"]), frozenset(["太陽", "金星"]), frozenset(["月", "金星"])}:
        return "attraction"
    if pair in {frozenset(["月", "土星"]), frozenset(["月", "冥王星"]), frozenset(["月", "天王星"]), frozenset(["水星", "月"])}:
        return "emotional_safety"
    if pair in {frozenset(["太陽", "土星"]), frozenset(["火星", "土星"]), frozenset(["水星", "火星"])}:
        return "conflict_repair"
    if pair in {frozenset(["金星", "土星"])}:
        return "long_term_stability"
    return "growth"


def assign_aspect_to_section(aspects: list[dict]) -> dict[str, list[dict]]:
    assigned = {k: [] for k in SYNASTRY_SECTION_TITLES}
    used_keys: set[tuple[frozenset[str], str]] = set()
    for asp in aspects:
        pair = frozenset([asp.get("planet1"), asp.get("planet2")])
        key = (pair, asp.get("aspect"))
        if key in used_keys:
            continue
        priorities = PAIR_SECTION_PRIORITY.get(pair)
        if not priorities:
            theme = classify_synastry_aspect_theme(asp)
            default_by_theme = {
                "attraction": "romance",
                "emotional_safety": "emotional",
                "conflict_repair": "friction",
                "long_term_stability": "stability",
                "growth": "growth",
            }
            priorities = [default_by_theme.get(theme, "growth")]
        target = next((sec for sec in priorities if len(assigned[sec]) < 2), priorities[0])
        assigned[target].append(asp)
        used_keys.add(key)
    return assigned


def choose_non_repeating_synastry_action_hint(section_key: str, used_hints: set[str], aspects: list[dict]) -> str | None:
    theme = THEME_BY_SECTION.get(section_key, "growth")
    pair_specific = []
    for asp in aspects:
        pair = frozenset([asp.get("planet1"), asp.get("planet2")])
        pair_specific.extend(ASPECT_HINTS_BY_PAIR.get(pair, {}).get(theme, []))
    for hint in pair_specific + ACTION_HINTS_BY_THEME.get(theme, []):
        if hint not in used_hints:
            used_hints.add(hint)
            return hint
    return None


def choose_non_repeating_relation_template(section_key: str, used_patterns: set[tuple[str, ...]]) -> list[str]:
    for pattern in SECTION_TEMPLATE_PATTERNS.get(section_key, [["aspect", "emotion"]]):
        key = tuple(pattern)
        if key not in used_patterns:
            used_patterns.add(key)
            return pattern
    return SECTION_TEMPLATE_PATTERNS.get(section_key, [["aspect", "emotion"]])[0]



SYNASTRY_ASPECT_TEMPLATES = {
    frozenset(["太陽", "月"]): {
        "harmonious": "太陽と月が調和すると、片方が方向性を示し、もう片方が気持ちを受け止める流れが自然に作られます。",
        "hard": "太陽と月がハードだと、励ましのつもりの言葉がプレッシャーに聞こえやすく、気持ちの波と行動の速度がずれやすいでしょう。",
    },
    frozenset(["金星", "火星"]): {
        "harmonious": "金星と火星が噛み合うと、会話やしぐさのテンポだけで惹かれ合いやすく、恋愛スイッチが入りやすい関係です。",
        "hard": "金星と火星がハードだと、惹かれ方は強いのに距離の詰め方が噛み合わず、熱量の差で揺れやすくなります。",
    },
    frozenset(["月", "土星"]): {
        "harmonious": "月と土星の調和は『この人といると落ち着く』という実感を育て、感情を丁寧に扱える信頼関係を作ります。",
        "hard": "月と土星が緊張すると、弱音を飲み込みやすく、安心したい場面ほど距離が出やすい配置です。",
    },
    frozenset(["月", "冥王星"]): {
        "harmonious": "月と冥王星が強く結びつくと、表面だけでは終わらない深い共感が起き、忘れにくい絆になりやすいでしょう。",
        "hard": "月と冥王星がハードだと、愛情と不安が同時に強まり、相手の気配に敏感になりすぎることがあります。",
    },
    frozenset(["水星", "火星"]): {
        "harmonious": "水星と火星が調和すると、話し合いから行動への移行が早く、計画を現実にしやすい関係です。",
        "hard": "水星と火星がハードだと、議論が勝ち負けになりやすく、正論ほど角が立ちやすい傾向があります。",
    },
}

def synthesize_synastry_aspect(asp: dict) -> str:
    p1, p2 = asp.get("planet1"), asp.get("planet2")
    aspect = asp.get("aspect")
    pair_key = frozenset([p1, p2])
    category = "harmonious" if aspect in {"コンジャンクション", "トライン", "セクスタイル"} else "hard"
    pair_templates = SYNASTRY_ASPECT_TEMPLATES.get(pair_key, {})
    lead = pair_templates.get(category, f"{p1}と{p2}は関係運用のテンポ調整を学びやすい組み合わせです。")
    enriched = interpret_aspect(asp, mode="synastry")
    return (
        f"{enriched['identity']}。{lead}"
        f" 心理ダイナミクス: {enriched['psychological_dynamic']}。"
        f" 生活現象: {enriched['life_manifestation']}。"
        f" 実践ガイド: {enriched['practical_guidance']}。"
    )


def _syn_house_overlay(chart1: list[dict], cusps1: list[float], chart2: list[dict]) -> list[str]:
    targets = {"太陽", "月", "金星", "火星"}
    lines = []
    for obj in chart2:
        if obj.get("planet") not in targets:
            continue
        house = get_house(float(obj.get("longitude", 0.0)), cusps1)
        if house in {4, 7, 8, 10}:
            p = obj.get("planet")
            if house == 4:
                lines.append(f"- 相手の{p}があなたの第4ハウスに入ると、外では平気でも二人きりになると本音が出やすく、居場所としての安心を求めやすくなります。")
            elif house == 7:
                lines.append(f"- 相手の{p}があなたの第7ハウスに入ると、相手を『対等なパートナー』として強く意識しやすく、関係を正式に整えたい気持ちが高まりやすいでしょう。")
            elif house == 8:
                lines.append(f"- 相手の{p}があなたの第8ハウスに入ると、軽い関係のつもりでも感情や欲求が深く動きやすく、惹かれ方が強いぶん不安も出やすくなります。")
            elif house == 10:
                lines.append(f"- 相手の{p}があなたの第10ハウスに入ると、将来像や仕事観に影響しやすく、二人の関係が社会的な目標と結びつきやすくなります。")
    return lines[:4]


def _pick_barnum_line(section_key: str, used: set[str]) -> str | None:
    for line in SYNASTRY_BARNUM_LINES.get(section_key, []):
        if line not in used:
            used.add(line)
            return line
    return None


def _append_synastry_section(lines: list[str], section_key: str, aspects: list[dict], used_barnum: set[str], used_hints: set[str], used_patterns: set[tuple[str, ...]]) -> None:
    lines.append("\n" + SYNASTRY_SECTION_TITLES[section_key])
    pattern = choose_non_repeating_relation_template(section_key, used_patterns)
    barnum = _pick_barnum_line(section_key, used_barnum)
    hint = choose_non_repeating_synastry_action_hint(section_key, used_hints, aspects)
    warning = "- 衝突を避けるより、回復の手順を先に決めるほど関係の消耗が減ります。"

    for item in pattern:
        if item == "aspect":
            for asp in aspects[:2]:
                lines.append(f"- {synthesize_synastry_aspect(asp)}")
        elif item == "emotion" and barnum:
            lines.append(f"- {barnum}")
        elif item == "hint" and hint:
            lines.append(f"- 行動ヒント: {hint}")
        elif item == "warning":
            lines.append(warning)
        elif item == "hint_only" and hint:
            lines.append(f"- 行動ヒント: {hint}")

    if not aspects and section_key in {"attraction_reason", "emotional", "romance", "friction"}:
        lines.append("- 今回は該当アスペクトが少なめですが、日常のやり取りの質を整えると体感は十分に変わります。")

    for summary in SECTION_SUMMARY_LINES.get(section_key, [])[:2]:
        lines.append(f"- {summary}")


def generate_synastry_interpretation(
    person1_chart: list,
    person2_chart: list,
    synastry_aspects: list,
    person1_name: str = "あなた",
    person2_name: str = "相手",
    person1_cusps: list[float] | None = None,
) -> str:
    lines = generate_report_header("synastry", person_name=person1_name, person2_name=person2_name)
    used_barnum, used_hints, used_patterns = set(), set(), set()

    deduped_aspects = dedupe_aspects(synastry_aspects)
    filtered_aspects = [a for a in deduped_aspects if should_show_minor_aspect(a, detailed_mode=False)]
    selected = [a for a in filtered_aspects if frozenset([a.get("planet1"), a.get("planet2")]) in SYN_PRIORITY_PAIRS]
    selected = sorted(
        selected,
        key=lambda x: (
            SYN_PRIORITY_PAIRS.index(frozenset([x.get("planet1"), x.get("planet2")])) if frozenset([x.get("planet1"), x.get("planet2")]) in SYN_PRIORITY_PAIRS else 99,
            float(x.get("orb", 99.0)),
        ),
    )

    section_aspects = assign_aspect_to_relationship_theme(selected)
    for section_key in ["attraction_reason", "emotional", "romance", "friction", "stability", "growth"]:
        _append_synastry_section(lines, section_key, section_aspects.get(section_key, []), used_barnum, used_hints, used_patterns)

    if USE_USCS_PHASE:
        syn_phase = calculate_synastry_phase_metrics(person1_chart, person2_chart)
        lines.append("\n【相性の補助指標（波長の重なり）】")
        lines.append(f"- 全体同期度: {syn_phase['relationship_phase_score']:.2f}")
        lines.append(f"- 感情結合: {syn_phase['emotional_phase_coupling']:.2f} / 引力結合: {syn_phase['attraction_phase_coupling']:.2f}")
        lines.append(f"- {syn_phase['phase_narrative']}")
        for pair in syn_phase.get("strongest_phase_pairs", [])[:2]:
            lines.append(f"- {pair['pair']}は『{pair['uscs_label']}』で、波長が噛み合いやすい組み合わせです。")

    if person1_cusps:
        overlays = _syn_house_overlay(person1_chart, person1_cusps, person2_chart)
        if overlays:
            lines.append("\n【ハウスオーバーレイ】")
            lines.extend(overlays)

    lines.append("\n" + "=" * 60)
    lines.append("※この相性レポートは2人の天体配置に基づく自動生成テキストです。")
    summary_lines = [
        _aspect_focus_line("関係の焦点", selected[0] if selected else None, mode="synastry"),
        f"関係運用の軸: 全体同期度は {syn_phase['relationship_phase_score']:.2f} で、感情結合 {syn_phase['emotional_phase_coupling']:.2f} / 引力結合 {syn_phase['attraction_phase_coupling']:.2f} が参考になります。" if USE_USCS_PHASE and syn_phase else None,
        "読みどころ: 『惹かれやすさ』と『長続きの運用』を分けて読むほど、相性の使い方が安定します。",
    ]
    action_lines = [
        choose_non_repeating_synastry_action_hint("emotional", set(), section_aspects.get("emotional", [])),
        choose_non_repeating_synastry_action_hint("stability", set(), section_aspects.get("stability", [])),
        "衝突を避けるより、回復の手順を先に決めておくと関係の消耗を減らしやすくなります。",
    ]
    note_lines = [
        "強い attraction があっても、返信速度や距離感の運用が噛み合うかは別軸として確認すると判断がぶれにくいです。",
    ]
    return _apply_report_quality_frame(
        "\n".join(lines),
        mode="synastry",
        summary_lines=summary_lines,
        action_lines=action_lines,
        note_lines=note_lines,
    )

def generate_progressed_interpretation(chart: list, aspects_sets: list, composite_sets: list, person_name: str = "あなた") -> str:
    progressed_chart = normalize_node_objects(chart)
    header = generate_report_header("progressed", person_name=person_name)
    lines = header[:]
    progressed_themes = generate_progressed_theme(progressed_chart)

    lines.append("\n【最近の内面テーマ】")
    for line in progressed_themes:
        lines.append(f"- {line}")

    lines.append("\n【時期の読み替え（生活現象）】")
    for p_obj in sorted([x for x in progressed_chart if x.get("planet") in MAIN_INTERPRET_PLANETS], key=lambda x: x.get("house", 99))[:2]:
        life_events = translate_life_event(int(p_obj.get("house", 0)))
        lines.append(f"- 最近は{p_obj.get('planet')}のテーマが『{' / '.join(life_events[:3])}』に出やすく、以前より生活設計そのものを更新したくなりやすいでしょう。")

    lines.append("\n【アスペクトが示す最近の学習テーマ】")
    gathered_aspects = [asp for aspects, _title in aspects_sets for asp in dedupe_aspects(aspects)]
    priority_aspects = [asp for asp in gathered_aspects if asp.get("aspect") in MAJOR_ASPECTS] or gathered_aspects
    top_aspects = sorted(priority_aspects, key=_aspect_priority_score)[:4]
    for asp in top_aspects:
        lines.append(f"- {synthesize_aspect(asp, mode='progressed')}")
    if not top_aspects:
        lines.append("- 最近は大きな外圧より、内側の納得感を整えることが進展の鍵です。")

    lines.append("\n【この時期の活かし方】")
    lines.append("- 最近は『以前より合わない進め方』を1つやめるだけでも、内面変化に現実が追いつきやすくなります。")
    lines.append("- 今は、タスク管理より先に感情ログを整えるほど、判断の質が安定します。")
    lines.append("\n" + "=" * 60)
    lines.append("※このプログレスレポートは二次進行チャートの時期性に基づく自動生成テキストです。")
    summary_lines = [
        f"内面変化の軸: {progressed_themes[0]}" if progressed_themes else None,
        _aspect_focus_line("最近の学習テーマ", top_aspects[0] if top_aspects else None, mode="progressed"),
        "実務の見方: 『何を増やすべきか』より『何が今は合わなくなったか』を見ると判断しやすい時期です。",
    ]
    action_lines = [
        "以前なら回せたやり方で違和感が出る部分を1つだけ棚卸しし、今週は更新候補を試してください。",
        _first_aspect_action(top_aspects[0] if top_aspects else None, mode="progressed"),
        "感情ログを短く残し、判断が安定した日と崩れた日の差を見つけると使いやすいです。",
    ]
    note_lines = [
        "プログレスは外側の派手な出来事より、納得の仕方や気持ちの重心がどう変わるかに注目すると読みやすいです。",
    ]
    return _apply_report_quality_frame(
        "\n".join(dedupe_similar_lines(lines)),
        mode="progressed",
        summary_lines=summary_lines,
        action_lines=action_lines,
        note_lines=note_lines,
    )

def build_transit_timing_window(asp: dict, window: float = 2.0) -> str:
    orb = float(asp.get("orb", 99.0))
    if orb > window:
        return f"現在オーブ{orb:.2f}°で、作用の立ち上がり前後に位置しています（実務上の有効窓 ±{window:.0f}°）。"
    return f"現在オーブ{orb:.2f}°で、実務上の有効窓（±{window:.0f}°）に入っており、出来事として体感しやすい時期です。"


def generate_transit_interpretation(chart: list, aspects_sets: list, composite_sets: list, person_name: str = "あなた") -> str:
    header = generate_report_header("transit", person_name=person_name)
    theme = extract_transit_theme(aspects_sets)
    base = _build_natal_style_interpretation(chart, aspects_sets, composite_sets, person_name, header, mode="transit")
    all_aspects = [asp for aspects, _ in aspects_sets for asp in dedupe_aspects(aspects)]
    priority_aspects = [asp for asp in all_aspects if asp.get("aspect") in MAJOR_ASPECTS] or all_aspects
    top_aspect = sorted(priority_aspects, key=_aspect_priority_score)[0] if priority_aspects else None
    timing_line = f"- タイミング窓: {build_transit_timing_window(top_aspect)}" if top_aspect else "- タイミング窓: 主要ヒットは穏やかで、準備フェーズとして使いやすい時期です。"
    hit_line = (
        f"- ナタルヒット: {top_aspect.get('planet1')}にトランジット{top_aspect.get('planet2')}が{top_aspect.get('aspect')}。"
        if top_aspect
        else "- ナタルヒット: 目立つ単発ヒットより、複数要因の重なりで現象化しやすい局面です。"
    )
    report_text = base + f"\n\n【トランジット視点の補足】\n- 今の外部テーマ: {theme}。\n{hit_line}\n{timing_line}\n- 現象を急いで評価するより、反応の良い行動を3週間単位で残すほど運気を使いやすくなります。"
    summary_lines = [
        f"外部テーマ: {theme}。",
        hit_line.replace("- ", ""),
        timing_line.replace("- ", ""),
    ]
    action_lines = [
        _first_aspect_action(top_aspect, mode="transit"),
        "反応の良い行動だけを3週間単位で残すと、時期の波を実務へ落とし込みやすくなります。",
        "大きな決断は一発で固めるより、締切と検証回数を細かく切るとブレにくいです。",
    ]
    note_lines = [
        "トランジットは『今すぐ全部変えるべき』という意味ではなく、追い風と負荷の発生地点を知る補助線です。",
    ]
    return _apply_report_quality_frame(
        report_text,
        mode="transit",
        summary_lines=summary_lines,
        action_lines=action_lines,
        note_lines=note_lines,
    )


def generate_triple_interpretation(natal_chart: list, progress_chart: list, transit_chart: list, aspect_sets: list, person_name: str = "あなた") -> str:
    header = generate_report_header("triple", person_name=person_name)
    natal_theme, progressed_theme, integrated = generate_triple_synthesis(natal_chart, progress_chart, aspect_sets)
    triple_phase = calculate_triple_phase_metrics(natal_chart, progress_chart, transit_chart) if USE_USCS_PHASE else None
    lines = header + [
        "\n1. 本質（ネイタル）",
        f"- {natal_theme}",
        "\n2. 現在の内面（プログレス）",
        f"- {progressed_theme}",
        "\n3. 外部環境（トランジット）",
        f"- {extract_transit_theme(aspect_sets)}。",
        "\n4. 統合ポイント",
        f"- {integrated}",
        "\n5. 実践アクション",
        "- 今は短期成果より、行動の再現性を優先して『毎週同じ振り返りフォーマット』を運用すると流れが安定します。",
    ]
    if triple_phase:
        lines.extend([
            "\n6. 三層の焦点化（補助指標）",
            f"- 三層共鳴度: {triple_phase['triple_phase_resonance']:.2f} / 三層緊張度: {triple_phase['triple_phase_tension']:.2f}",
            f"- テーマ集中度: {triple_phase['triple_phase_focus']:.2f}",
            f"- {triple_phase['phase_narrative']}",
        ])
    lines.extend([
        "\n" + "=" * 60,
        "※このトリプルレポートはネイタル・プログレス・トランジット統合に基づく自動生成テキストです。",
    ])
    summary_lines = [
        f"本質の軸: {natal_theme}",
        f"最近の変化: {progressed_theme}",
        f"今の統合テーマ: {integrated}",
    ]
    action_lines = [
        "今週は『続けること1つ・減らすこと1つ・試すこと1つ』を同じフォーマットで記録してください。",
        "複数テーマが同時に動く時期ほど、全部を最適化するより最重要テーマを1つ決める方が安定します。",
        f"三層共鳴度 {triple_phase['triple_phase_resonance']:.2f} / 緊張度 {triple_phase['triple_phase_tension']:.2f} を、行動量より優先順位調整の参考値として扱うと実務向きです。" if triple_phase else None,
    ]
    note_lines = [
        "トリプルは情報量が多いので、『本質』『最近の内面』『外部タイミング』を別々に読み、最後に重なる点だけ拾うと判断しやすいです。",
    ]
    return _apply_report_quality_frame(
        "\n".join(lines),
        mode="triple",
        summary_lines=summary_lines,
        action_lines=action_lines,
        note_lines=note_lines,
    )

def generate_natal_interpretation(natal_chart: list, aspects_sets: list, composite_sets: list, person_name: str = "あなた") -> str:
    chart = normalize_node_objects(natal_chart)
    sun = next((p for p in chart if p.get("planet") == "太陽"), None)
    moon = next((p for p in chart if p.get("planet") == "月"), None)
    report_text = _build_natal_style_interpretation(
        natal_chart,
        aspects_sets,
        composite_sets,
        person_name,
        generate_report_header("natal", person_name=person_name),
        mode="natal",
    )
    summary_lines = [
        _placement_focus_line("核の軸", sun),
        _placement_focus_line("感情の軸", moon),
        f"全体バランス: {summarize_element_mode_balance(chart)}",
    ]
    action_lines = [
        _first_placement_action(sun),
        _first_placement_action(moon),
        *suggest_actions_for_balance(chart, limit=2),
    ]
    note_lines = [
        "出生図は長期的な癖と強みを見る地図なので、短期の気分や一時的な不調と切り分けて読むと活かしやすいです。",
    ]
    return _apply_report_quality_frame(
        report_text,
        mode="natal",
        summary_lines=summary_lines,
        action_lines=action_lines,
        note_lines=note_lines,
    )


def generate_interpretation(
    natal_chart: list,
    aspects_sets: list,
    composite_sets: list,
    person_name: str = "あなた",
    chart_mode: str = "natal",
    context: dict | None = None,
) -> str:
    mode = LEGACY_MODE_ALIASES.get(chart_mode, chart_mode)
    context = context or {}
    if mode == "natal":
        return generate_natal_interpretation(natal_chart, aspects_sets, composite_sets, person_name)
    if mode == "progressed":
        return generate_progressed_interpretation(natal_chart, aspects_sets, composite_sets, person_name)
    if mode == "transit":
        return generate_transit_interpretation(natal_chart, aspects_sets, composite_sets, person_name)
    if mode == "triple":
        return generate_triple_interpretation(
            natal_chart=context.get("natal_chart", natal_chart),
            progress_chart=context.get("progress_chart", natal_chart),
            transit_chart=context.get("transit_chart", natal_chart),
            aspect_sets=aspects_sets,
            person_name=person_name,
        )
    if mode == "synastry":
        return generate_synastry_interpretation(
            person1_chart=context.get("person1_chart", natal_chart),
            person2_chart=context.get("person2_chart", []),
            synastry_aspects=context.get("synastry_aspects", aspects_sets[0][0] if aspects_sets else []),
            person1_name=person_name,
            person2_name=context.get("person2_name", "相手"),
            person1_cusps=context.get("person1_cusps"),
        )
    raise ValueError(f"未対応の chart_mode: {chart_mode}")




def build_chart_from_input(
    date_tuple: tuple[int, int, int],
    time_str: str,
    tz_offset: int | float,
    lat: float,
    lon: float,
    *,
    hsys: str = "P",
    include_asteroids: bool = True,
) -> dict:
    """Notebook など外部UI向け: 入力値からチャートと付帯情報を構築して返す。"""
    ut = convert_time_to_ut_decimal_hours(time_str, tz_offset)
    julian_day = swe.julday(date_tuple[0], date_tuple[1], date_tuple[2], ut)
    chart, cusps = calculate_astrology_data(
        julian_day,
        lat,
        lon,
        hsys=hsys,
        include_asteroids=include_asteroids,
    )
    return {
        "chart": chart,
        "cusps": cusps,
        "julian_day": julian_day,
        "date": date_tuple,
        "time": time_str,
        "tz": tz_offset,
        "lat": lat,
        "lon": lon,
    }


def _resolve_output_dir() -> Path:
    output_dir = os.getenv("RESULT_OUTPUT_DIR")
    if output_dir:
        path = Path(output_dir).expanduser().resolve()
    else:
        path = Path(__file__).resolve().parent / "data" / "results"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save_report_files(
    result_text: str,
    interpretation_text: str,
    *,
    llm_prompt_text: str | None = None,
    compact_data: dict[str, object] | None = None,
) -> dict:
    output_dir = _resolve_output_dir()
    result_path = output_dir / "astrology_result.txt"
    interpretation_path = output_dir / "astrology_interpretation.txt"
    with result_path.open("w", encoding="utf-8") as f:
        f.write(result_text)
    with interpretation_path.open("w", encoding="utf-8") as f:
        f.write(interpretation_text)
    payload = {"result_path": str(result_path), "interpretation_path": str(interpretation_path)}
    if llm_prompt_text is not None:
        llm_prompt_path = output_dir / "astrology_llm_prompt.txt"
        llm_prompt_path.write_text(llm_prompt_text, encoding="utf-8")
        payload["llm_prompt_path"] = str(llm_prompt_path)
    if compact_data is not None:
        compact_data_path = output_dir / "astrology_compact_data.json"
        compact_data_path.write_text(json.dumps(compact_data, ensure_ascii=False, indent=2), encoding="utf-8")
        payload["compact_data_path"] = str(compact_data_path)
    return payload


def _header_meta_for_target(mode: str, target: dict) -> dict:
    return {
        "target_datetime": f"{target['date'][0]:04d}-{target['date'][1]:02d}-{target['date'][2]:02d} {target['time']} (UTC{target['tz']:+g})",
        "target_location": f"lat={target['lat']}, lon={target['lon']}",
        "chart_mode": mode,
    }


def run_natal_report(target: dict, *, person_name: str = "あなた", include_minor_aspects: bool = True, include_composite_aspects: bool = True) -> dict:
    chart = target["chart"]
    aspects = calculate_aspects(chart, chart, include_minor_aspects=include_minor_aspects)
    composites = calculate_composite_aspects(chart, COMPOSITE_ASPECTS) if include_composite_aspects else []
    placement_interpretations = [interpret_planet_position(p) for p in chart if p.get("planet") in MAIN_INTERPRET_PLANETS]
    aspect_interpretations = [interpret_aspect(a, mode="natal") for a in aspects[:8]]
    interp = generate_natal_interpretation(
        chart,
        [(aspects, "ネイタル")],
        [(composites, "複合")],
        person_name=person_name,
    )
    result_text = synthesize_interpretation(
        placements=placement_interpretations,
        aspects=aspect_interpretations,
        mode="natal",
    )
    compact_data = build_compact_interpretation_payload(
        placements=placement_interpretations,
        aspects=aspect_interpretations,
        mode="natal",
        subject_label=person_name,
    )
    llm_prompt_text = build_llm_reading_prompt(compact_data, mode="natal")
    files = _save_report_files(result_text, interp, llm_prompt_text=llm_prompt_text, compact_data=compact_data)
    return {
        "chart": chart,
        "aspects": aspects,
        "composites": composites,
        "interpretation": interp,
        "result_text": result_text,
        "llm_prompt_text": llm_prompt_text,
        "compact_data": compact_data,
        **files,
    }


def run_progressed_report(natal: dict, progressed: dict, *, person_name: str = "あなた", include_minor_aspects: bool = True) -> dict:
    aspects = calculate_aspects(natal["chart"], progressed["chart"], include_minor_aspects=include_minor_aspects)
    ctx = _header_meta_for_target("progressed", progressed)
    interp = generate_progressed_interpretation(progressed["chart"], [(aspects, "ネイタル×プログレス")], [], person_name=person_name)
    placement_interpretations = [interpret_planet_position(p) for p in progressed["chart"] if p.get("planet") in MAIN_INTERPRET_PLANETS]
    aspect_interpretations = [interpret_aspect(a, mode="progressed") for a in aspects[:8]]
    result_text = synthesize_interpretation(
        placements=placement_interpretations,
        aspects=aspect_interpretations,
        mode="progressed",
    )
    compact_data = build_compact_interpretation_payload(
        placements=placement_interpretations,
        aspects=aspect_interpretations,
        mode="progressed",
        subject_label=person_name,
    )
    llm_prompt_text = build_llm_reading_prompt(compact_data, mode="progressed")
    files = _save_report_files(result_text, interp, llm_prompt_text=llm_prompt_text, compact_data=compact_data)
    return {
        "chart": progressed["chart"],
        "aspects": aspects,
        "composites": [],
        "interpretation": interp,
        "result_text": result_text,
        "llm_prompt_text": llm_prompt_text,
        "compact_data": compact_data,
        "context": ctx,
        **files,
    }


def run_transit_report(natal: dict, transit: dict, *, person_name: str = "あなた", include_minor_aspects: bool = True) -> dict:
    aspects = calculate_aspects(natal["chart"], transit["chart"], include_minor_aspects=include_minor_aspects)
    ctx = _header_meta_for_target("transit", transit)
    interp = generate_transit_interpretation(transit["chart"], [(aspects, "ネイタル×トランジット")], [], person_name=person_name)
    placement_interpretations = [interpret_planet_position(p) for p in transit["chart"] if p.get("planet") in MAIN_INTERPRET_PLANETS]
    aspect_interpretations = [interpret_aspect(a, mode="transit") for a in aspects[:8]]
    result_text = synthesize_interpretation(
        placements=placement_interpretations,
        aspects=aspect_interpretations,
        mode="transit",
    )
    compact_data = build_compact_interpretation_payload(
        placements=placement_interpretations,
        aspects=aspect_interpretations,
        mode="transit",
        subject_label=person_name,
    )
    llm_prompt_text = build_llm_reading_prompt(compact_data, mode="transit")
    files = _save_report_files(result_text, interp, llm_prompt_text=llm_prompt_text, compact_data=compact_data)
    return {
        "chart": transit["chart"],
        "aspects": aspects,
        "composites": [],
        "interpretation": interp,
        "result_text": result_text,
        "llm_prompt_text": llm_prompt_text,
        "compact_data": compact_data,
        "context": ctx,
        **files,
    }


def run_triple_report(natal: dict, progressed: dict, transit: dict, *, person_name: str = "あなた", include_minor_aspects: bool = True) -> dict:
    aspects = [
        (calculate_aspects(natal["chart"], natal["chart"], include_minor_aspects=include_minor_aspects), "ネイタル内"),
        (calculate_aspects(natal["chart"], progressed["chart"], include_minor_aspects=include_minor_aspects), "ネイタル×プログレス"),
        (calculate_aspects(natal["chart"], transit["chart"], include_minor_aspects=include_minor_aspects), "ネイタル×トランジット"),
    ]
    triple_phase = calculate_triple_phase_metrics(natal["chart"], progressed["chart"], transit["chart"]) if USE_USCS_PHASE else None
    interp = generate_triple_interpretation(
        natal_chart=natal["chart"],
        progress_chart=progressed["chart"],
        transit_chart=transit["chart"],
        aspect_sets=aspects,
        person_name=person_name,
    )
    flat_aspects = [aspect for aspect_set, _label in aspects for aspect in aspect_set]
    placement_interpretations = [interpret_planet_position(p) for p in natal["chart"] if p.get("planet") in MAIN_INTERPRET_PLANETS]
    aspect_interpretations = [interpret_aspect(a, mode="triple") for a in flat_aspects[:8]]
    result_text = synthesize_interpretation(
        placements=placement_interpretations,
        aspects=aspect_interpretations,
        mode="triple",
    )
    compact_data = build_compact_interpretation_payload(
        placements=placement_interpretations,
        aspects=aspect_interpretations,
        mode="triple",
        subject_label=person_name,
    )
    llm_prompt_text = build_llm_reading_prompt(compact_data, mode="triple")
    files = _save_report_files(result_text, interp, llm_prompt_text=llm_prompt_text, compact_data=compact_data)
    return {
        "chart": natal["chart"],
        "aspects": aspects,
        "composites": [],
        "interpretation": interp,
        "result_text": result_text,
        "llm_prompt_text": llm_prompt_text,
        "compact_data": compact_data,
        "uscs_phase": triple_phase,
        **files,
    }


def run_synastry_report(person1: dict, person2: dict, *, person1_name: str = "あなた", person2_name: str = "相手", include_minor_aspects: bool = True) -> dict:
    syn = calculate_aspects(person1["chart"], person2["chart"], include_minor_aspects=include_minor_aspects)
    syn_phase = calculate_synastry_phase_metrics(person1["chart"], person2["chart"]) if USE_USCS_PHASE else None
    interp = generate_synastry_interpretation(
        person1_chart=person1["chart"],
        person2_chart=person2["chart"],
        synastry_aspects=syn,
        person1_name=person1_name,
        person2_name=person2_name,
        person1_cusps=person1.get("cusps"),
    )
    overlay_interpretations = interpret_house_overlay(person1["chart"], person2["chart"], person1.get("cusps"))
    placement_interpretations = [interpret_planet_position(p) for p in person1["chart"] if p.get("planet") in MAIN_INTERPRET_PLANETS]
    aspect_interpretations = [interpret_aspect(a, mode="synastry") for a in syn[:8]]
    result_text = synthesize_interpretation(
        placements=placement_interpretations,
        aspects=aspect_interpretations,
        overlays=overlay_interpretations,
        mode="synastry",
    )
    compact_data = build_compact_interpretation_payload(
        placements=placement_interpretations,
        aspects=aspect_interpretations,
        overlays=overlay_interpretations,
        mode="synastry",
        subject_label=f"{person1_name} × {person2_name}",
    )
    llm_prompt_text = build_llm_reading_prompt(compact_data, mode="synastry")
    files = _save_report_files(result_text, interp, llm_prompt_text=llm_prompt_text, compact_data=compact_data)
    return {
        "chart": person1["chart"],
        "aspects": syn,
        "composites": [],
        "interpretation": interp,
        "result_text": result_text,
        "llm_prompt_text": llm_prompt_text,
        "compact_data": compact_data,
        "uscs_phase": syn_phase,
        **files,
    }

def run_report_by_mode(
    chart_mode: str,
    *,
    natal: dict,
    progressed: dict | None = None,
    transit: dict | None = None,
    person2: dict | None = None,
    person_name: str = "あなた",
    person2_name: str = "相手",
    include_minor_aspects: bool = True,
    include_composite_aspects: bool = True,
) -> dict:
    """chart_mode に応じてレポート作成関数を振り分ける統一入口。"""
    mode = LEGACY_MODE_ALIASES.get(chart_mode, chart_mode)
    if mode == "natal":
        return run_natal_report(
            natal,
            person_name=person_name,
            include_minor_aspects=include_minor_aspects,
            include_composite_aspects=include_composite_aspects,
        )
    if mode == "progressed":
        if progressed is None:
            raise ValueError("progressed モードでは progressed 引数が必要です")
        return run_progressed_report(natal, progressed, person_name=person_name, include_minor_aspects=include_minor_aspects)
    if mode == "transit":
        if transit is None:
            raise ValueError("transit モードでは transit 引数が必要です")
        return run_transit_report(natal, transit, person_name=person_name, include_minor_aspects=include_minor_aspects)
    if mode == "triple":
        if progressed is None or transit is None:
            raise ValueError("triple モードでは progressed と transit 引数が必要です")
        return run_triple_report(natal, progressed, transit, person_name=person_name, include_minor_aspects=include_minor_aspects)
    if mode == "synastry":
        if person2 is None:
            raise ValueError("synastry モードでは person2 引数が必要です")
        return run_synastry_report(
            natal,
            person2,
            person1_name=person_name,
            person2_name=person2_name,
            include_minor_aspects=include_minor_aspects,
        )
    raise ValueError(f"未対応の chart_mode: {chart_mode}")


def _build_chart_data_from_config(date_tuple, time_str, tz_offset, lat, lon):
    """
    設定ブロックのパラメータからジュリアン日を計算して辞書で返す（差分追加）。
    """
    ut = convert_time_to_ut_decimal_hours(time_str, tz_offset)
    jd = swe.julday(date_tuple[0], date_tuple[1], date_tuple[2], ut)
    return {'julian_day': jd, 'lat': lat, 'lon': lon}


def _prompt_with_default(prompt: str, default: str) -> str:
    entered = input(f"{prompt} [{default}]: ").strip()
    return entered or default


def _cli_defaults() -> dict:
    return {
        "chart_mode": chart_mode,
        "person_name": PERSON_NAME,
        "date": f"{NATAL_DATE[0]:04d}-{NATAL_DATE[1]:02d}-{NATAL_DATE[2]:02d}",
        "time": NATAL_TIME,
        "timezone": str(NATAL_TZ),
        "lat": str(NATAL_LAT),
        "lon": str(NATAL_LON),
        "progressed_date": f"{PROGRESS_DATE[0]:04d}-{PROGRESS_DATE[1]:02d}-{PROGRESS_DATE[2]:02d}",
        "progressed_time": PROGRESS_TIME,
        "transit_date": f"{TRANSIT_DATE[0]:04d}-{TRANSIT_DATE[1]:02d}-{TRANSIT_DATE[2]:02d}",
        "transit_time": TRANSIT_TIME,
        "person2_date": f"{PERSON2_DATE[0]:04d}-{PERSON2_DATE[1]:02d}-{PERSON2_DATE[2]:02d}",
        "person2_time": PERSON2_TIME,
        "person2_timezone": str(PERSON2_TZ),
        "person2_lat": str(PERSON2_LAT),
        "person2_lon": str(PERSON2_LON),
        "person2_name": "相手",
    }


def _parse_date_string(value: str) -> tuple[int, int, int]:
    dt = datetime.strptime(value, "%Y-%m-%d")
    return dt.year, dt.month, dt.day


def _chart_from_cli_values(date_value: str, time_value: str, timezone_value: str, lat_value: str, lon_value: str) -> dict:
    return build_chart_from_input(
        _parse_date_string(date_value),
        time_value,
        float(timezone_value),
        float(lat_value),
        float(lon_value),
        hsys=hsys,
        include_asteroids=include_asteroids,
    )


def _collect_cli_inputs() -> dict:
    defaults = _cli_defaults()
    mode = _prompt_with_default("chart mode (natal/progressed/transit/triple/synastry)", defaults["chart_mode"])
    payload = {
        "chart_mode": mode,
        "person_name": _prompt_with_default("person name", defaults["person_name"]),
        "date": _prompt_with_default("birth date YYYY-MM-DD", defaults["date"]),
        "time": _prompt_with_default("birth time HH:MM", defaults["time"]),
        "timezone": _prompt_with_default("timezone offset", defaults["timezone"]),
        "lat": _prompt_with_default("latitude", defaults["lat"]),
        "lon": _prompt_with_default("longitude", defaults["lon"]),
        "person2_name": defaults["person2_name"],
    }
    if mode in {"progressed", "triple"}:
        payload["progressed_date"] = _prompt_with_default("progressed date YYYY-MM-DD", defaults["progressed_date"])
        payload["progressed_time"] = _prompt_with_default("progressed time HH:MM", defaults["progressed_time"])
    if mode in {"transit", "triple"}:
        payload["transit_date"] = _prompt_with_default("transit date YYYY-MM-DD", defaults["transit_date"])
        payload["transit_time"] = _prompt_with_default("transit time HH:MM", defaults["transit_time"])
    if mode == "synastry":
        payload["person2_name"] = _prompt_with_default("second person name", defaults["person2_name"])
        payload["person2_date"] = _prompt_with_default("second person date YYYY-MM-DD", defaults["person2_date"])
        payload["person2_time"] = _prompt_with_default("second person time HH:MM", defaults["person2_time"])
        payload["person2_timezone"] = _prompt_with_default("second person timezone offset", defaults["person2_timezone"])
        payload["person2_lat"] = _prompt_with_default("second person latitude", defaults["person2_lat"])
        payload["person2_lon"] = _prompt_with_default("second person longitude", defaults["person2_lon"])
    return payload


def _run_cli_report(cli_values: dict) -> dict:
    natal = _chart_from_cli_values(
        cli_values["date"],
        cli_values["time"],
        cli_values["timezone"],
        cli_values["lat"],
        cli_values["lon"],
    )
    progressed = None
    transit = None
    person2 = None
    mode = LEGACY_MODE_ALIASES.get(cli_values["chart_mode"], cli_values["chart_mode"])
    if mode in {"progressed", "triple"}:
        progressed = _chart_from_cli_values(
            cli_values["progressed_date"],
            cli_values["progressed_time"],
            cli_values["timezone"],
            cli_values["lat"],
            cli_values["lon"],
        )
    if mode in {"transit", "triple"}:
        transit = _chart_from_cli_values(
            cli_values["transit_date"],
            cli_values["transit_time"],
            cli_values["timezone"],
            cli_values["lat"],
            cli_values["lon"],
        )
    if mode == "synastry":
        person2 = _chart_from_cli_values(
            cli_values["person2_date"],
            cli_values["person2_time"],
            cli_values["person2_timezone"],
            cli_values["person2_lat"],
            cli_values["person2_lon"],
        )
    return run_report_by_mode(
        mode,
        natal=natal,
        progressed=progressed,
        transit=transit,
        person2=person2,
        person_name=cli_values["person_name"],
        person2_name=cli_values.get("person2_name", "相手"),
        include_minor_aspects=include_minor_aspects,
        include_composite_aspects=include_composite_aspects,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Local astrology report generator")
    parser.add_argument("--non-interactive", action="store_true", help="Use repository defaults without prompts")
    args = parser.parse_args()

    cli_values = _cli_defaults() if args.non_interactive else _collect_cli_inputs()
    result = _run_cli_report(cli_values)
    print(result["interpretation"])
    print(f"[SAVE] result summary: {result['result_path']}")
    print(f"[SAVE] interpretation: {result['interpretation_path']}")

# =======================
# 3. 使用例セクション
# =======================

if __name__ == "__main__":
    main()
