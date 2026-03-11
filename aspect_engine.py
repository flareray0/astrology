from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ASPECT_TYPE_MAP = {
    "コンジャンクション": {"angle": 0, "type": "conjunction"},
    "セクスタイル": {"angle": 60, "type": "sextile"},
    "スクエア": {"angle": 90, "type": "square"},
    "トライン": {"angle": 120, "type": "trine"},
    "オポジション": {"angle": 180, "type": "opposition"},
}

ASPECT_TYPE_MEANING = {
    "conjunction": "融合と増幅が同時に起こり、テーマが強く前面化する角度",
    "sextile": "機会を活かすほど協力作用が伸びる角度",
    "square": "摩擦が課題を可視化し、成長圧を生む角度",
    "trine": "自然な流れで才能が巡回しやすい角度",
    "opposition": "両極の視点を往復し、他者を鏡に統合を学ぶ角度",
}

ELEMENT_MAP = {
    "牡羊座": "火", "獅子座": "火", "射手座": "火",
    "牡牛座": "地", "乙女座": "地", "山羊座": "地",
    "双子座": "風", "天秤座": "風", "水瓶座": "風",
    "蟹座": "水", "蠍座": "水", "魚座": "水",
}

HOUSE_INTERACTION = {
    (3, 10): "学びや発信が職業評価に直結し、報連相の質が成果差を生みやすい",
    (4, 7): "家庭観と対人契約の整合性が問われ、関係ルール更新が起こりやすい",
    (2, 8): "個人資産と共有資産の設計が連動し、金銭ポリシーの調整が必要になりやすい",
    (1, 7): "自己主張と協調の境界管理が課題化し、対話設計で結果が変わりやすい",
}

PLANET_MAX_ORB = {"太陽": 8.0, "月": 8.0}
OUTER_PLANETS = {"天王星", "海王星", "冥王星"}

MODE_FOCUS = {
    "natal": "長期的な性格パターンとして反復されやすい",
    "progressed": "内面の成熟テーマとして体感されやすい",
    "transit": "現実イベントとして短中期で顕在化しやすい",
    "triple": "本質・内面・外部環境の接点として統合課題が見えやすい",
    "synastry": "関係性ダイナミクスとして相互反応に表れやすい",
}

OPENERS = ["この配置は", "この角度では", "この組み合わせは", "この天体関係は"]


def _max_orb(planet1: str, planet2: str) -> float:
    max_orb = 6.0
    if planet1 in PLANET_MAX_ORB or planet2 in PLANET_MAX_ORB:
        max_orb = 8.0
    if planet1 in OUTER_PLANETS and planet2 in OUTER_PLANETS:
        max_orb = 4.0
    return max_orb


@lru_cache(maxsize=1)
def load_aspect_rules() -> dict:
    with (Path(__file__).resolve().parent / "aspect_rules.json").open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_planet_pairs() -> dict:
    with (Path(__file__).resolve().parent / "aspect_planet_pairs.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def classify_aspect(aspect_data: dict) -> dict:
    aspect_name = aspect_data.get("aspect", "")
    mapped = ASPECT_TYPE_MAP.get(aspect_name, {"angle": None, "type": "other"})
    orb = float(aspect_data.get("orb", 99.0))
    planet1 = aspect_data.get("planet1", "")
    planet2 = aspect_data.get("planet2", "")
    max_orb = _max_orb(planet1, planet2)
    strength = max(0.0, 1 - (orb / max_orb))
    return {
        "type": mapped["type"],
        "angle": mapped["angle"],
        "orb": orb,
        "strength": round(strength, 3),
        "planets": [planet1, planet2],
        "signs": [aspect_data.get("planet1_sign"), aspect_data.get("planet2_sign")],
        "houses": [aspect_data.get("planet1_house"), aspect_data.get("planet2_house")],
        "max_orb": max_orb,
    }


def strength_narrative(orb: float) -> str:
    if orb < 1:
        return "この配置は非常に強く作用しています"
    if orb <= 3:
        return "この配置は明確に働きやすいでしょう"
    return "この配置は背景として静かに影響しています"


def sign_interaction(sign1: str, sign2: str) -> str:
    pair = frozenset([ELEMENT_MAP.get(sign1), ELEMENT_MAP.get(sign2)])
    if pair == frozenset(["火", "風"]):
        return "行動力と発想力が接続しやすく、着手から改善までの回転が速くなる"
    if pair == frozenset(["水", "地"]):
        return "感情の安定と実務感覚が連動し、生活設計を固めやすい"
    if pair == frozenset(["火", "水"]):
        return "情熱と繊細さの速度差が出やすく、意思表示タイミングの調整が要点になる"
    if pair == frozenset(["地", "風"]):
        return "構想を現実タスクへ落とし込みやすく、設計と実行の往復が効く"
    return "価値観の違いが学習資源になり、役割分担を更新しやすい"


def house_interaction(house1: int, house2: int) -> str:
    key = tuple(sorted((int(house1), int(house2))))
    return HOUSE_INTERACTION.get(key, "日常導線の接点で課題が顕在化し、運用ルールを再設計しやすい")


def _pair_key(planet1: str, planet2: str) -> str:
    ordered = sorted([planet1, planet2])
    return f"{ordered[0]}|{ordered[1]}"


def _rule_key(planet1: str, planet2: str, aspect_type: str) -> str:
    return f"{_pair_key(planet1, planet2)}|{aspect_type}"


def _aspect_identity(p1: str, p2: str, aspect_name: str, orb: float) -> str:
    return f"{p1}と{p2}の{aspect_name}（オーブ{orb:.2f}°）"


def _choose_opener(p1: str, p2: str, aspect_type: str) -> str:
    seed = sum(ord(ch) for ch in f"{p1}{p2}{aspect_type}")
    return OPENERS[seed % len(OPENERS)]


def interpret_aspect(aspect_data: dict, mode: str = "natal") -> dict:
    classified = classify_aspect(aspect_data)
    p1, p2 = classified["planets"]
    aspect_name = aspect_data.get("aspect", "")
    aspect_type = classified["type"]

    rules = load_aspect_rules()
    pairs = load_planet_pairs()
    rule = rules.get(_rule_key(p1, p2, aspect_type), {})
    pair_info = pairs.get(_pair_key(p1, p2), pairs.get("default", {}))

    life_patterns = pair_info.get("life_patterns", ["行動結果のばらつき"])
    mode_focus = MODE_FOCUS.get(mode, MODE_FOCUS["natal"])
    opener = _choose_opener(p1, p2, aspect_type)

    psychological_dynamic = rule.get(
        "psychology",
        f"{pair_info.get('core_tension', '価値観の調整')}。{ASPECT_TYPE_MEANING.get(aspect_type, '関係性を更新する角度')}。",
    )
    life_manifestation = rule.get(
        "life_manifestation",
        f"{life_patterns[0]}を起点に、{life_patterns[1]}へ連鎖しやすい。",
    )
    practical_guidance = rule.get(
        "advice",
        f"{pair_info.get('growth_theme', '運用ルールを明確化する')}。",
    )

    return {
        "classification": classified,
        "identity": _aspect_identity(p1, p2, aspect_name, classified["orb"]),
        "opener": opener,
        "psychological_dynamic": psychological_dynamic,
        "life_manifestation": life_manifestation,
        "timing_or_intensity": f"{strength_narrative(classified['orb'])}。{mode_focus}。",
        "practical_guidance": practical_guidance,
        "sign_interaction": sign_interaction(classified["signs"][0], classified["signs"][1]),
        "house_interaction": house_interaction(classified["houses"][0], classified["houses"][1]),
        "life_events": life_patterns[:3],
    }
