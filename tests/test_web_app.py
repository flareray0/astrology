from fastapi.testclient import TestClient

from web.app import app


client = TestClient(app)


def test_root_page_renders():
    response = client.get("/")
    assert response.status_code == 200
    assert "ローカル星読みレポート" in response.text
    assert "占いモード" in response.text
    assert "要点サマリー" in response.text
    assert "LLM読み解き用プロンプト" in response.text
    assert "圧縮データ" in response.text


def test_natal_api_report_returns_text_and_paths():
    response = client.post(
        "/api/report/natal",
        data={
            "person_name": "Test",
            "birth_date": "1984-11-15",
            "birth_time": "11:27",
            "latitude": "37.38",
            "longitude": "140.18",
            "timezone": "9",
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["mode"] == "natal"
    assert payload["mode_label"] == "ネイタルチャート（出生図）"
    assert "太陽" in payload["interpretation"]
    assert "【出生傾向の要点サマリー】" in payload["result_text"]
    assert "対象モード: ネイタルチャート（出生図）" in payload["result_text"]
    assert "Interpretation synthesis" not in payload["result_text"]
    assert "以下の圧縮データだけを根拠に、日本語で読み解いてください。" in payload["llm_prompt_text"]
    assert payload["compact_data"]["対象モード"] == "ネイタルチャート（出生図）"
    assert payload["result_path"].endswith("astrology_result.txt")
    assert payload["llm_prompt_path"].endswith("astrology_llm_prompt.txt")
    assert payload["compact_data_path"].endswith("astrology_compact_data.json")


def test_synastry_api_report_returns_relationship_text():
    response = client.post(
        "/api/report/synastry",
        data={
            "person_name": "A",
            "birth_date": "1984-11-15",
            "birth_time": "11:27",
            "latitude": "37.38",
            "longitude": "140.18",
            "timezone": "9",
            "person2_name": "B",
            "person2_birth_date": "1967-05-13",
            "person2_birth_time": "00:00",
            "person2_latitude": "35.68",
            "person2_longitude": "139.65",
            "person2_timezone": "9",
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["mode"] == "synastry"
    assert payload["mode_label"] == "シナストリー（相性）"
    assert "相性レポート" in payload["interpretation"]
    assert "【相性の要点サマリー】" in payload["result_text"]
    assert "対象モード: シナストリー（相性）" in payload["result_text"]
    assert payload["compact_data"]["対象者"] == "A × B"
