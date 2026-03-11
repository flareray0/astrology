from aspect_engine import classify_aspect, interpret_aspect, strength_narrative


def test_classify_strength_for_tight_major_aspect():
    payload = {
        "planet1": "火星",
        "planet2": "土星",
        "aspect": "セクスタイル",
        "orb": 0.34,
        "planet1_sign": "水瓶座",
        "planet2_sign": "魚座",
        "planet1_house": 3,
        "planet2_house": 10,
    }
    classified = classify_aspect(payload)
    assert classified["type"] == "sextile"
    assert classified["strength"] > 0.9


def test_interpret_uses_pair_dictionary_and_layers():
    payload = {
        "planet1": "火星",
        "planet2": "土星",
        "aspect": "トライン",
        "orb": 1.2,
        "planet1_sign": "牡羊座",
        "planet2_sign": "双子座",
        "planet1_house": 4,
        "planet2_house": 7,
    }
    interpreted = interpret_aspect(payload, mode="natal")
    assert "推進力" in interpreted["psychological_dynamic"]
    assert "家庭観" in interpreted["house_interaction"]
    assert "行動力" in interpreted["sign_interaction"]
    assert interpreted["identity"].startswith("火星と土星")


def test_strength_narrative_buckets():
    assert "非常に強く" in strength_narrative(0.5)
    assert "明確に" in strength_narrative(2.0)
    assert "背景" in strength_narrative(4.0)


def test_mode_focus_changes_timing_line_for_transit():
    payload = {
        "planet1": "太陽",
        "planet2": "月",
        "aspect": "スクエア",
        "orb": 0.8,
        "planet1_sign": "牡羊座",
        "planet2_sign": "蟹座",
        "planet1_house": 1,
        "planet2_house": 7,
    }
    interpreted = interpret_aspect(payload, mode="transit")
    assert "現実イベント" in interpreted["timing_or_intensity"]
