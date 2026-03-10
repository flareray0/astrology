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
    複合アスペクト（ヨッド、グランドクロス等）は現在未実装。
    将来的に実装するまで、常に空リストを返します。
    """
    composite_found = []
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

    else:
        print("無効なモードが指定されています。'triple_chart' か 'synastry' を指定してください。")
