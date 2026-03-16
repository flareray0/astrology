from fastapi.testclient import TestClient

from web.app import app


client = TestClient(app)


def test_root_page_renders():
    response = client.get("/")
    assert response.status_code == 200
    assert "Astrology Local App" in response.text


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
    assert "太陽" in payload["interpretation"]
    assert payload["result_path"].endswith("astrology_result.txt")


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
    assert "相性レポート" in payload["interpretation"]
