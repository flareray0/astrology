import swisseph as swe
from datetime import datetime
from itertools import combinations

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

# エフェメリスのパスを設定
swe.set_ephe_path(r'/content/drive/MyDrive/ephe')

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
_ASPECT_INTERP = {
    'コンジャンクション': "{p1}と{p2}が重なり合い、その力は一つに融合しています。強烈な集中とエネルギーの統合をもたらします。",
    'オポジション':       "{p1}と{p2}は対極に位置し、緊張と引力が共存します。他者との関係や内なる葛藤を通じて成長が促されます。",
    'トライン':           "{p1}と{p2}は調和し、才能と恵みが自然に流れ込みます。創造性や幸運を引き寄せる力があります。",
    'スクエア':           "{p1}と{p2}の間には摩擦があります。困難を乗り越える意志と行動力を試される局面があるでしょう。",
    'セクスタイル':       "{p1}と{p2}は穏やかに協調し、機会と可能性の扉を開きます。",
    'クインカンクス（150°）': "{p1}と{p2}は不思議な緊張感を持ちます。調整と適応を重ねることで新たな統合が生まれます。",
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

def generate_interpretation(
    natal_chart: list,
    aspects_sets: list,
    composite_sets: list,
    person_name: str = "あなた",
) -> str:
    """
    チャート・アスペクト・複合アスペクトから占い師文体の解釈テキストを自動生成します。

    Args:
        natal_chart: ネイタルチャートデータ
        aspects_sets: [(aspects_list, '見出し'), ...] のリスト
        composite_sets: [(composite_list, '見出し'), ...] のリスト
        person_name: 対象者の名前（デフォルト「あなた」）

    Returns:
        str: 解釈テキスト
    """
    lines = []
    lines.append(f"＊ {person_name}の星読みレポート ＊")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)

    # 太陽・月・ASC の基本情報
    sun = next((p for p in natal_chart if p['planet'] == '太陽'), None)
    moon = next((p for p in natal_chart if p['planet'] == '月'), None)
    asc = next((p for p in natal_chart if p['planet'] == 'アセンダント'), None)

    lines.append("\n【基本的な性質】")
    if sun:
        lines.append(f"太陽は{sun['sign']}に位置しています。{sun['sign']}の本質的なエネルギーが、{person_name}の核となる自己表現を彩ります。")
    if moon:
        lines.append(f"月は{moon['sign']}に宿り、感情の深いところで{moon['sign']}の感受性が息づいています。")
    if asc:
        lines.append(f"アセンダントは{asc['sign']}。世界との接点において、{asc['sign']}の気質が自然と滲み出るでしょう。")

    # アスペクト解釈（メジャーのみ・最大10件）
    lines.append("\n【惑星同士の対話】")
    major_aspect_names = set(_ASPECT_INTERP.keys())
    interpreted = 0
    for aspects, title in aspects_sets:
        for asp in aspects:
            if asp['aspect'] not in major_aspect_names:
                continue
            tmpl = _ASPECT_INTERP.get(asp['aspect'])
            if tmpl:
                lines.append(tmpl.format(p1=asp['planet1'], p2=asp['planet2']))
                interpreted += 1
            if interpreted >= 10:
                break
        if interpreted >= 10:
            break
    if interpreted == 0:
        lines.append("主要なアスペクトは検出されませんでした。")

    # 複合アスペクト解釈
    lines.append("\n【特別な天体配置】")
    any_composite = False
    for composites, title in composite_sets:
        for comp in composites:
            tmpl = _COMPOSITE_INTERP.get(comp['type'])
            if tmpl:
                planets_str = "・".join(comp['planets'])
                lines.append(tmpl.format(planets=planets_str))
                any_composite = True
    if not any_composite:
        lines.append("今回は特別な複合パターンは検出されませんでした。")

    lines.append("\n" + "=" * 60)
    lines.append("※このレポートは天体配置に基づく自動生成テキストです。")

    return "\n".join(lines)


# =======================
# 3. 使用例セクション
# =======================

if __name__ == "__main__":
    if mode == 'triple_chart':
        print("=== 三重チャートの計算と表示 ===")

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
            person_name='あなた',
        )
        print(interp_text)
        with open('astrology_interpretation.txt', 'w', encoding='utf-8') as f:
            f.write(interp_text)
        print("[SAVE] 解釈レポートを保存しました: astrology_interpretation.txt")

    elif mode == 'synastry':
        print("=== シナストリーの計算と表示 ===")

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
            person_name='二人の関係',
        )
        print(interp_text)
        with open('astrology_interpretation.txt', 'w', encoding='utf-8') as f:
            f.write(interp_text)
        print("[SAVE] 解釈レポートを保存しました: astrology_interpretation.txt")

    else:
        print("無効なモードが指定されています。'triple_chart' か 'synastry' を指定してください。")
