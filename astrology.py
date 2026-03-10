import os
import swisseph as swe
from datetime import datetime
from itertools import combinations

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

# モードの指定（'triple_chart' または 'synastry'）
mode = 'triple_chart'

# エフェメリスのパスを設定（Webアプリから環境変数で切り替え可能）
swe.set_ephe_path(os.getenv('ASTROLOGY_EPHE_PATH', r'/content/drive/MyDrive/ephe'))

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
        print(f"ハウス計算中にエラーが発生しました: {e}")
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
            print(f"惑星 {planet_name} の処理中にエラーが発生しました: {e}")
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
        print(f"バーテクスの計算中にエラーが発生しました: {e}")

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
            print(f"特別なポイント {name} の処理中にエラーが発生しました: {e}")
            continue

    return astrology_data, cusps

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
        # メジャーアスペクト
        for aspect, (aspect_degree, orb) in MAJOR_ASPECTS.items():
            if abs(diff - aspect_degree) <= orb:
                aspects.append({
                    'planet1': planet1['planet'],
                    'planet2': planet2['planet'],
                    'aspect': aspect,
                    'planet1_sign': planet1['sign'],
                    'planet1_house': planet1['house'],
                    'planet2_sign': planet2['sign'],
                    'planet2_house': planet2['house'],
                    'exact': diff,
                    'orb': abs(diff - aspect_degree),
                    'planet1_retrograde': planet1['retrograde'],
                    'planet2_retrograde': planet2['retrograde']
                })
        # マイナーアスペクト
        if include_minor_aspects:
            for aspect, (aspect_degree, orb) in MINOR_ASPECTS.items():
                if abs(diff - aspect_degree) <= orb:
                    aspects.append({
                        'planet1': planet1['planet'],
                        'planet2': planet2['planet'],
                        'aspect': aspect,
                        'planet1_sign': planet1['sign'],
                        'planet1_house': planet1['house'],
                        'planet2_sign': planet2['sign'],
                        'planet2_house': planet2['house'],
                        'exact': diff,
                        'orb': abs(diff - aspect_degree),
                        'planet1_retrograde': planet1['retrograde'],
                        'planet2_retrograde': planet2['retrograde']
                    })
    return aspects

def calculate_composite_aspects(astro_data, composite_aspects_def):
    """
    複合アスペクト（ヨッド、グランドクロス、Tスクエア、グランドトライン、
    キート、ミスティックレクタングル、レクタングル、スター、ヴェース）を検出します。
    COMPOSITE_SKIP に含まれる感受点は除外します。
    """
    composite_found = []
    # 標準的占星術慣習に基づくフィルタリング
    filtered = [p for p in astro_data if p['planet'] not in COMPOSITE_SKIP]

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

    return composite_found
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

NODE_NORMALIZE_RULES = {
    "ドラゴンヘッド": {"alias_group": "node_head", "priority": 2},
    "トゥルーノード": {"alias_group": "node_head", "priority": 1},
    "ドラゴンテール": {"alias_group": "node_tail", "priority": 2},
    "トゥルーテール": {"alias_group": "node_tail", "priority": 1},
}

# True Node / Mean Node 系の重複を抑制する設定。
# False: 同一系統は優先順位の高い1つのみ表示
# True : ノード変種をそのまま残す
SHOW_TRUE_NODE_VARIANTS = False

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
    ("太陽", "蠍座"): "意志が深層心理・変容・真実追求へ向かい、極限状況ほど覚醒します",
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


def normalize_node_objects(chart: list[dict]) -> list[dict]:
    """ノード系の重複を優先順位ベースで正規化する。"""
    if SHOW_TRUE_NODE_VARIANTS:
        return chart

    grouped: dict[str, dict] = {}
    passthrough: list[dict] = []
    for obj in chart:
        rule = NODE_NORMALIZE_RULES.get(obj.get("planet"))
        if not rule:
            passthrough.append(obj)
            continue
        key = rule["alias_group"]
        prev = grouped.get(key)
        if not prev:
            grouped[key] = obj
            continue
        prev_pri = NODE_NORMALIZE_RULES[prev["planet"]]["priority"]
        if rule["priority"] > prev_pri:
            grouped[key] = obj
    normalized = passthrough + list(grouped.values())
    return normalized


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


def synthesize_planet_house(p: dict) -> str:
    """Planet × House の読みを返す。"""
    planet = p.get("planet", "")
    house = p.get("house", 0)
    return PLANET_HOUSE_MEANING.get(
        (planet, house),
        f"第{house}ハウス（{HOUSE_ARCHETYPE.get(house, '')}）でその力が日常に現れます",
    )


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


def suggest_actions_for_placement(p: dict, limit: int = 2) -> list[str]:
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
    return deduped[:limit]


def suggest_actions_for_aspect(asp: dict, limit: int = 1) -> list[str]:
    action = ACTIONS_BY_ASPECT_TYPE.get(asp.get("aspect"))
    return [action][:limit] if action else []


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


def synthesize_planet_sign_house(p: dict, suppress_sign_detail: bool = False) -> str:
    """Planet × Sign × House を統合文として生成する。"""
    planet = p.get("planet", "")
    sign = p.get("sign", "")
    house = p.get("house", 0)
    ps = synthesize_planet_sign(p, suppress_redundant=suppress_sign_detail)
    ph = synthesize_planet_house(p)
    motion = "内面で熟成してから形にする" if p.get("retrograde") else "行動しながら答えを磨く"
    return f"{planet}が{sign}の第{house}ハウス。{ps}。{ph}。{motion}タイプです。"


def dedupe_aspects(aspects: list[dict]) -> list[dict]:
    """同義に近いアスペクトを天体ペア×アスペクト種別で集約（最小オーブ優先）。"""
    best: dict[tuple, dict] = {}
    for asp in aspects:
        p1, p2 = asp.get("planet1"), asp.get("planet2")
        pair = tuple(sorted([p1, p2]))
        key = (pair, asp.get("aspect"))
        prev = best.get(key)
        if not prev or asp.get("orb", 999) < prev.get("orb", 999):
            best[key] = asp
    return sorted(best.values(), key=lambda x: x.get("orb", 999))


def dedupe_similar_lines(lines: list[str]) -> list[str]:
    seen = set()
    out = []
    for line in lines:
        key = line.replace("。", "").replace("、", "")[:40]
        if key not in seen:
            seen.add(key)
            out.append(line)
    return out


def synthesize_aspect(asp: dict) -> str:
    """Planet1 × Aspect × Planet2 の意味合成。"""
    p1 = asp.get("planet1")
    p2 = asp.get("planet2")
    aspect = asp.get("aspect")
    pair_theme = PLANET_PAIR_MEANING.get(frozenset([p1, p2]), f"{p1}と{p2}の関係")
    aspect_theme = ASPECT_MEANING.get(aspect, "固有の学習テーマを持つ角度")
    orb = float(asp.get("orb", 99.0))
    sign_hint = f"{asp.get('planet1_sign')}×{asp.get('planet2_sign')}"
    action = suggest_actions_for_aspect(asp)
    action_line = f" 活かし方のヒント: {action[0]}。" if action else ""
    return (
        f"{p1} {aspect} {p2}: {pair_theme}。{aspect_theme}。"
        f"オーブ{orb:.2f}°（{sign_hint}）。{action_line}"
    )


def generate_interpretation(
    natal_chart: list,
    aspects_sets: list,
    composite_sets: list,
    person_name: str = "あなた",
) -> str:
    """象徴合成レイヤーを用いた解釈テキストを生成する。"""
    chart = normalize_node_objects(natal_chart)
    lines = [
        f"＊ {person_name}の星読みレポート ＊",
        f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        "\n【核 / 人生テーマ】",
    ]

    sun = next((p for p in chart if p.get("planet") == "太陽"), None)
    moon = next((p for p in chart if p.get("planet") == "月"), None)
    asc = next((p for p in chart if p.get("planet") == "アセンダント"), None)
    seen_signs: set[str] = set()

    if sun:
        lines.append(f"- {synthesize_planet_sign_house(sun)}")
        lines.append(f"  {generate_barnum_line(sun)}")
        lines.append(f"  日常でやるなら: {' / '.join(suggest_actions_for_placement(sun))}")
        seen_signs.add(sun.get("sign"))
    if moon:
        lines.append(f"- {synthesize_planet_sign_house(moon, suppress_sign_detail=moon.get('sign') in seen_signs)}")
        lines.append(f"  {generate_barnum_line(moon)}")
        lines.append(f"  おすすめ行動: {' / '.join(suggest_actions_for_placement(moon))}")
        seen_signs.add(moon.get("sign"))
    if asc:
        lines.append(f"- 社会への見え方: {synthesize_planet_sign_house(asc, suppress_sign_detail=asc.get('sign') in seen_signs)}")

    lines.append(f"- 全体バランス: {summarize_element_mode_balance(chart)}")
    lines.append(f"  活かし方のヒント: {' / '.join(suggest_actions_for_balance(chart))}")

    lines.append("\n【資質（感情と対人傾向）】")
    for pname in ["月", "金星", "火星"]:
        p = next((obj for obj in chart if obj.get("planet") == pname), None)
        if p:
            lines.append(f"- {synthesize_planet_sign_house(p, suppress_sign_detail=p.get('sign') in seen_signs)}")
            barnum = generate_barnum_line(p)
            if barnum:
                lines.append(f"  {barnum}")
            lines.append(f"  活かし方のヒント: {' / '.join(suggest_actions_for_placement(p, limit=1))}")
            seen_signs.add(p.get("sign"))

    major_aspects = []
    for aspects, _title in aspects_sets:
        major_aspects.extend([a for a in aspects if a.get("aspect") in ASPECT_MEANING])
    major_aspects = dedupe_aspects(major_aspects)

    lines.append("\n【才能の流れ（自然に伸びる資質）】")
    talent_lines = []
    for asp in major_aspects:
        if asp.get("aspect") in {"トライン", "セクスタイル", "コンジャンクション"}:
            talent_lines.append(f"- {synthesize_aspect(asp)}")
        if len(talent_lines) >= 4:
            break
    lines.extend(dedupe_similar_lines(talent_lines) or ["- 才能は『やってみる→調整する』の反復で自然に育ちます。"])

    lines.append("\n【課題（葛藤しやすいテーマ）】")
    challenge_lines = []
    for asp in major_aspects:
        if asp.get("aspect") in {"スクエア", "オポジション", "クインカンクス（150°）"}:
            challenge_lines.append(f"- {synthesize_aspect(asp)}")
        if len(challenge_lines) >= 4:
            break
    lines.extend(dedupe_similar_lines(challenge_lines) or ["- 大きな葛藤は少なめ。だからこそ、自分から課題設定すると成長が早まります。"])

    lines.append("\n【特別な複合配置】")
    any_composite = False
    for composites, _title in composite_sets:
        for comp in composites:
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

def _build_chart_data_from_config(date_tuple, time_str, tz_offset, lat, lon):
    """
    設定ブロックのパラメータからジュリアン日を計算して辞書で返す（差分追加）。
    """
    ut = convert_time_to_ut_decimal_hours(time_str, tz_offset)
    jd = swe.julday(date_tuple[0], date_tuple[1], date_tuple[2], ut)
    return {'julian_day': jd, 'lat': lat, 'lon': lon}

# =======================
# 3. 使用例セクション
# =======================

if __name__ == "__main__":
    if mode == 'triple_chart':
        print("=== 三重チャートの計算と表示 ===")

        # -----------------------
        # USE_CONFIG_BLOCK で切り替え（差分追加）
        # -----------------------
        if USE_CONFIG_BLOCK:
            natal_data    = _build_chart_data_from_config(NATAL_DATE,    NATAL_TIME,    NATAL_TZ,    NATAL_LAT,    NATAL_LON)
            progress_data = _build_chart_data_from_config(PROGRESS_DATE, PROGRESS_TIME, PROGRESS_TZ, PROGRESS_LAT, PROGRESS_LON)
            transit_data  = _build_chart_data_from_config(TRANSIT_DATE,  TRANSIT_TIME,  TRANSIT_TZ,  TRANSIT_LAT,  TRANSIT_LON)
            person_name   = PERSON_NAME
        else:
            # -----------------------
            # ネイタルデータ（例）
            # -----------------------
            ntime = convert_time_to_ut_decimal_hours("11:27", 9)
            natal_data = {
                'julian_day': swe.julday(1984, 11, 15, ntime),
                'lat': 37.38,
                'lon': 140.18
            }

            # -----------------------
            # プログレスデータ（例）
            # -----------------------
            ptime = convert_time_to_ut_decimal_hours("00:00", 9)
            progress_data = {
                'julian_day': swe.julday(1984, 12, 26, ptime),
                'lat': 37.38,
                'lon': 140.18
            }

            # -----------------------
            # トランジットデータ（例）
            # -----------------------
            ttime = convert_time_to_ut_decimal_hours("00:00", 9)
            transit_data = {
                'julian_day': swe.julday(2026, 2, 12, ttime),
                'lat': 37.38,
                'lon': 140.18
            }
            person_name = "あなた"

        # チャートを計算
        natal_chart, natal_cusps = calculate_astrology_data(
            natal_data['julian_day'], natal_data['lat'], natal_data['lon'],
            hsys=hsys, include_asteroids=include_asteroids
        )
        progress_chart, progress_cusps = calculate_astrology_data(
            progress_data['julian_day'], progress_data['lat'], progress_data['lon'],
            hsys=hsys, include_asteroids=include_asteroids
        )
        transit_chart, transit_cusps = calculate_astrology_data(
            transit_data['julian_day'], transit_data['lat'], transit_data['lon'],
            hsys=hsys, include_asteroids=include_asteroids
        )

        # アスペクト計算（natal vs natalなど）
        natal_natal_aspects = calculate_aspects(natal_chart, natal_chart, include_minor_aspects)
        natal_progress_aspects = calculate_aspects(natal_chart, progress_chart, include_minor_aspects)
        natal_transit_aspects = calculate_aspects(natal_chart, transit_chart, include_minor_aspects)
        progress_progress_aspects = calculate_aspects(progress_chart, progress_chart, include_minor_aspects)
        progress_transit_aspects = calculate_aspects(progress_chart, transit_chart, include_minor_aspects)
        transit_transit_aspects = calculate_aspects(transit_chart, transit_chart, include_minor_aspects)

        # 結果表示
        print_chart(natal_chart, "ネイタルチャート")
        print_chart(progress_chart, "プログレスチャート")
        print_chart(transit_chart, "トランジットチャート")

        # ハウスカスプ例
        print_house_cusps(natal_cusps, "ネイタル")
        print_house_cusps(progress_cusps, "プログレス")
        print_house_cusps(transit_cusps, "トランジット")

        # アスペクトの出力例
        aspect_sets = [
            (natal_natal_aspects, "ネイタルチャート内のアスペクト"),
            (natal_progress_aspects, "ネイタルとプログレスのアスペクト"),
            (natal_transit_aspects, "ネイタルとトランジットのアスペクト"),
            #(progress_progress_aspects, "プログレスチャート内のアスペクト"),
            (progress_transit_aspects, "プログレスとトランジットのアスペクト"),
            #(transit_transit_aspects, "トランジットチャート内のアスペクト"),
        ]
        for aspects, aspect_title in aspect_sets:
            print_aspects(aspects, aspect_title)

        # --- 結果テキスト保存（差分追加） ---
        save_results_to_text(
            charts={
                'ネイタルチャート': natal_chart,
                'プログレスチャート': progress_chart,
                'トランジットチャート': transit_chart,
            },
            aspects_sets=[
                (natal_natal_aspects,    'ネイタルチャート内のアスペクト'),
                (natal_progress_aspects, 'ネイタルとプログレスのアスペクト'),
                (natal_transit_aspects,  'ネイタルとトランジットのアスペクト'),
                (progress_transit_aspects, 'プログレスとトランジットのアスペクト'),
            ],
            composite_sets=[
                (calculate_composite_aspects(natal_chart, COMPOSITE_ASPECTS), 'ネイタル複合アスペクト'),
            ],
            filepath='astrology_result.txt',
        )

        # --- 占い師文体レポート生成（差分追加） ---
        interp_text = generate_interpretation(
            natal_chart=natal_chart,
            aspects_sets=[
                (natal_natal_aspects,    'ネイタルチャート内のアスペクト'),
                (natal_transit_aspects,  'ネイタルとトランジットのアスペクト'),
            ],
            composite_sets=[
                (calculate_composite_aspects(natal_chart, COMPOSITE_ASPECTS), 'ネイタル複合アスペクト'),
            ],
            person_name=person_name,
        )
        print(interp_text)
        with open('astrology_interpretation.txt', 'w', encoding='utf-8') as f:
            f.write(interp_text)
        print("[SAVE] 解釈レポートを保存しました: astrology_interpretation.txt")

    elif mode == 'synastry':
        print("=== シナストリーの計算と表示 ===")

        if USE_CONFIG_BLOCK:
            person1_data = _build_chart_data_from_config(NATAL_DATE,   NATAL_TIME,   NATAL_TZ,   NATAL_LAT,   NATAL_LON)
            person2_data = _build_chart_data_from_config(PERSON2_DATE, PERSON2_TIME, PERSON2_TZ, PERSON2_LAT, PERSON2_LON)
            person_name  = PERSON_NAME
        else:
            # -----------------------
            # 二人分のネイタルデータ（例）
            # -----------------------
            time_str1 = "11:27"
            timezone_offset1 = 9
            ut_time1 = convert_time_to_ut_decimal_hours(time_str1, timezone_offset1)
            person1_data = {
                'julian_day': swe.julday(1984, 11, 15, ut_time1),
                'lat': 37.38,
                'lon': 140.18
            }

            time_str2 = "00:00"
            timezone_offset2 = 9
            ut_time2 = convert_time_to_ut_decimal_hours(time_str2, timezone_offset2)
            person2_data = {
                'julian_day': swe.julday(1967, 5, 13, ut_time2),
                'lat': 35.68,
                'lon': 139.65
            }
            person_name = "二人の関係"

        # 二人分のチャート計算
        person1_chart, person1_cusps = calculate_astrology_data(
            person1_data['julian_day'], person1_data['lat'], person1_data['lon'],
            hsys=hsys, include_asteroids=include_asteroids
        )
        person2_chart, person2_cusps = calculate_astrology_data(
            person2_data['julian_day'], person2_data['lat'], person2_data['lon'],
            hsys=hsys, include_asteroids=include_asteroids
        )

        # シナストリーアスペクト
        synastry_aspects = calculate_aspects(
            person1_chart, person2_chart, include_minor_aspects=include_minor_aspects
        )

        # 複合アスペクト（必要に応じて実装）
        composite_patterns_synastry = []
        if include_composite_aspects:
            combined_chart = person1_chart + person2_chart
            composite_patterns_synastry = calculate_composite_aspects(
                combined_chart, COMPOSITE_ASPECTS
            )

        # 出力
        print_chart(person1_chart, "俺のネイタルチャート")
        print_chart(person2_chart, "相手のネイタルチャート")
        print_aspects(synastry_aspects, "シナストリーアスペクト")

        if include_composite_aspects:
            print_composite_aspects(composite_patterns_synastry, "シナストリー")

        # --- 結果テキスト保存（差分追加） ---
        save_results_to_text(
            charts={
                '俺のネイタルチャート': person1_chart,
                '相手のネイタルチャート': person2_chart,
            },
            aspects_sets=[
                (synastry_aspects, 'シナストリーアスペクト'),
            ],
            composite_sets=[
                (composite_patterns_synastry, 'シナストリー複合アスペクト'),
            ],
            filepath='astrology_result.txt',
        )

        # --- 占い師文体レポート生成（差分追加） ---
        interp_text = generate_interpretation(
            natal_chart=person1_chart,
            aspects_sets=[
                (synastry_aspects, 'シナストリーアスペクト'),
            ],
            composite_sets=[
                (composite_patterns_synastry, 'シナストリー複合アスペクト'),
            ],
            person_name=person_name,
        )
        print(interp_text)
        with open('astrology_interpretation.txt', 'w', encoding='utf-8') as f:
            f.write(interp_text)
        print("[SAVE] 解釈レポートを保存しました: astrology_interpretation.txt")

    else:
        print("無効なモードが指定されています。'triple_chart' か 'synastry' を指定してください。")
