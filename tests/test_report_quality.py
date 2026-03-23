import pytest

from astrology import build_chart_from_input, run_report_by_mode


def _build_sample_payloads() -> dict:
    natal = build_chart_from_input((1984, 11, 15), "11:27", 9, 37.38, 140.18)
    progressed = build_chart_from_input((2026, 3, 23), "00:00", 9, 37.38, 140.18)
    transit = build_chart_from_input((2026, 3, 23), "00:00", 9, 37.38, 140.18)
    person2 = build_chart_from_input((1967, 5, 13), "00:00", 9, 35.68, 139.65)
    return {
        "natal": natal,
        "progressed": progressed,
        "transit": transit,
        "person2": person2,
    }


@pytest.mark.parametrize(
    ("mode", "expected_marker"),
    [
        ("natal", "【核 / 人生テーマ】"),
        ("progressed", "【最近の内面テーマ】"),
        ("transit", "【トランジット視点の補足】"),
        ("triple", "1. 本質（ネイタル）"),
        ("synastry", "【1. 二人が惹かれやすい理由】"),
    ],
)
def test_report_modes_include_consistent_quality_sections(mode: str, expected_marker: str) -> None:
    charts = _build_sample_payloads()
    payload = run_report_by_mode(
        chart_mode=mode,
        natal=charts["natal"],
        progressed=charts["progressed"],
        transit=charts["transit"],
        person2=charts["person2"],
        person_name="Test",
        person2_name="Partner",
    )
    interpretation = payload["interpretation"]
    result_text = payload["result_text"]
    assert "【まずひとこと】" in interpretation
    assert "【最初に押さえたい要点】" in interpretation
    assert "【実践ガイド】" in interpretation
    assert "【読み方メモ】" in interpretation
    assert "むずかしく考えなくて大丈夫" in interpretation or "全部を同時に理解しなくて大丈夫" in interpretation or "今の自分の変化をやさしく確認" in interpretation or "時期運は怖がるためではなく" in interpretation or "相性は合う合わないを決めつけるためではなく" in interpretation
    assert expected_marker in interpretation
    assert "※この" in interpretation
    assert "【星どうしの大事な関係】" in result_text
    assert "やってみるコツ:" in result_text


def test_progressed_report_keeps_existing_section_and_new_focus_summary() -> None:
    charts = _build_sample_payloads()
    payload = run_report_by_mode(
        chart_mode="progressed",
        natal=charts["natal"],
        progressed=charts["progressed"],
        person_name="Test",
    )
    interpretation = payload["interpretation"]
    assert "内面変化の軸" in interpretation
    assert "【この時期の活かし方】" in interpretation


def test_natal_aspect_text_is_shorter_and_more_gentle() -> None:
    charts = _build_sample_payloads()
    payload = run_report_by_mode(
        chart_mode="natal",
        natal=charts["natal"],
        person_name="Test",
    )

    interpretation = payload["interpretation"]
    assert "生活現象:" not in interpretation
    assert "強度と時期:" not in interpretation
    assert "ハウス連動:" not in interpretation
    assert "やってみるコツ:" in interpretation
