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

ELEMENT_MAP = {
    "牡羊座": "火", "獅子座": "火", "射手座": "火",
    "牡牛座": "地", "乙女座": "地", "山羊座": "地",
    "双子座": "風", "天秤座": "風", "水瓶座": "風",
    "蟹座": "水", "蠍座": "水", "魚座": "水",
}

HOUSE_INTERACTION = {
    (3, 10): "学び・発信が仕事や評価に直結しやすい流れ",
    (4, 7): "家庭の価値観がパートナーシップ運用に影響する流れ",
    (2, 8): "個人資産と共有資産のバランス調整が課題になりやすい流れ",
    (1, 7): "自己主張と対人協調の境界線がテーマになる流れ",
}

PLANET_MAX_ORB = {
    "太陽": 8.0,
    "月": 8.0,
}

OUTER_PLANETS = {"天王星", "海王星", "冥王星"}


def _max_orb(planet1: str, planet2: str) -> float:
    max_orb = 6.0
    if planet1 in PLANET_MAX_ORB or planet2 in PLANET_MAX_ORB:
        max_orb = 8.0
    if planet1 in OUTER_PLANETS and planet2 in OUTER_PLANETS:
        max_orb = 4.0
    return max_orb


@lru_cache(maxsize=1)
def load_aspect_rules() -> dict:
    rule_path = Path(__file__).resolve().parent / "aspect_rules.json"
    with rule_path.open("r", encoding="utf-8") as f:
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
    e1 = ELEMENT_MAP.get(sign1)
    e2 = ELEMENT_MAP.get(sign2)
    pair = frozenset([e1, e2])
    if pair == frozenset(["火", "風"]):
        return "行動と発想が連動し、展開が速くなりやすい組み合わせ"
    if pair == frozenset(["水", "地"]):
        return "感情と現実感覚が噛み合い、安定運用しやすい組み合わせ"
    if pair == frozenset(["火", "水"]):
        return "情熱と感情の温度差が出やすく、反応速度の調整が鍵になる組み合わせ"
    if pair == frozenset(["地", "風"]):
        return "論理と実務を接続しやすく、計画が実装に落ちやすい組み合わせ"
    return "価値観の違いが学習機会になり、関わり方を更新しやすい組み合わせ"


def house_interaction(house1: int, house2: int) -> str:
    key = tuple(sorted((int(house1), int(house2))))
    return HOUSE_INTERACTION.get(key, "日常領域どうしの接点で、現実課題として可視化されやすい流れ")


def _rule_key(planet1: str, planet2: str, aspect_type: str) -> str:
    ordered = sorted([planet1, planet2])
    return f"{ordered[0]}|{ordered[1]}|{aspect_type}"


def interpret_aspect(aspect_data: dict) -> dict:
    classified = classify_aspect(aspect_data)
    p1, p2 = classified["planets"]
    rules = load_aspect_rules()
    rule = rules.get(_rule_key(p1, p2, classified["type"]), rules.get("default", {}))

    return {
        "classification": classified,
        "psychology": rule.get("psychology", f"{p1}と{p2}の組み合わせが、内面テーマを強調しやすい配置"),
        "life_manifestation": rule.get("life_manifestation", "対人・仕事・習慣の選択に連鎖的な影響が出やすい時期"),
        "advice": rule.get("advice", "反応が良い行動を小さく継続し、検証ログを残す"),
        "strength_narrative": strength_narrative(classified["orb"]),
        "sign_interaction": sign_interaction(classified["signs"][0], classified["signs"][1]),
        "house_interaction": house_interaction(classified["houses"][0], classified["houses"][1]),
    }
