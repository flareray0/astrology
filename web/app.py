import logging
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from astrology import build_chart_from_input, run_report_by_mode

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Astrology Local App")

if (BASE_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def _default_form_values() -> dict:
    return {
        "chart_mode": "natal",
        "person_name": "あなた",
        "birth_date": "1984-11-15",
        "birth_time": "11:27",
        "latitude": "37.38",
        "longitude": "140.18",
        "timezone": "9",
        "progressed_date": datetime.now().strftime("%Y-%m-%d"),
        "progressed_time": "00:00",
        "transit_date": datetime.now().strftime("%Y-%m-%d"),
        "transit_time": "00:00",
        "person2_name": "相手",
        "person2_birth_date": "1967-05-13",
        "person2_birth_time": "00:00",
        "person2_latitude": "35.68",
        "person2_longitude": "139.65",
        "person2_timezone": "9",
    }


def _parse_date(value: str) -> tuple[int, int, int]:
    dt = datetime.strptime(value, "%Y-%m-%d")
    return dt.year, dt.month, dt.day


def _build_primary_chart(date_value: str, time_value: str, timezone: float, latitude: float, longitude: float) -> dict:
    return build_chart_from_input(
        date_tuple=_parse_date(date_value),
        time_str=time_value,
        tz_offset=timezone,
        lat=latitude,
        lon=longitude,
    )


def _build_report(
    chart_mode: str,
    person_name: str,
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    timezone: float,
    progressed_date: str | None = None,
    progressed_time: str | None = None,
    transit_date: str | None = None,
    transit_time: str | None = None,
    person2_name: str = "相手",
    person2_birth_date: str | None = None,
    person2_birth_time: str | None = None,
    person2_latitude: float | None = None,
    person2_longitude: float | None = None,
    person2_timezone: float | None = None,
) -> dict:
    natal = _build_primary_chart(birth_date, birth_time, timezone, latitude, longitude)
    progressed = None
    transit = None
    person2 = None

    if chart_mode in {"progressed", "triple"}:
        progressed = _build_primary_chart(progressed_date or birth_date, progressed_time or birth_time, timezone, latitude, longitude)
    if chart_mode in {"transit", "triple"}:
        transit = _build_primary_chart(transit_date or birth_date, transit_time or birth_time, timezone, latitude, longitude)
    if chart_mode == "synastry":
        if None in {person2_birth_date, person2_birth_time, person2_latitude, person2_longitude, person2_timezone}:
            raise ValueError("synastry mode requires complete second person input")
        person2 = _build_primary_chart(
            person2_birth_date,
            person2_birth_time,
            float(person2_timezone),
            float(person2_latitude),
            float(person2_longitude),
        )

    return run_report_by_mode(
        chart_mode=chart_mode,
        natal=natal,
        progressed=progressed,
        transit=transit,
        person2=person2,
        person_name=person_name,
        person2_name=person2_name,
    )


def _render_page(request: Request, form_values: dict, report_payload: dict | None = None, error_message: str | None = None) -> HTMLResponse:
    context = {
        "request": request,
        "form": {**_default_form_values(), **form_values},
        "report": report_payload["interpretation"] if report_payload else "",
        "result_text": report_payload.get("result_text", "") if report_payload else "",
        "result_path": report_payload.get("result_path", "") if report_payload else "",
        "interpretation_path": report_payload.get("interpretation_path", "") if report_payload else "",
        "error_message": error_message,
    }
    return templates.TemplateResponse(request, "index.html", context)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return _render_page(request, _default_form_values())


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/report", response_class=HTMLResponse)
async def report_html(
    request: Request,
    chart_mode: str = Form("natal"),
    person_name: str = Form("あなた"),
    birth_date: str = Form(...),
    birth_time: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    timezone: float = Form(...),
    progressed_date: str = Form(""),
    progressed_time: str = Form("00:00"),
    transit_date: str = Form(""),
    transit_time: str = Form("00:00"),
    person2_name: str = Form("相手"),
    person2_birth_date: str = Form(""),
    person2_birth_time: str = Form("00:00"),
    person2_latitude: float = Form(0),
    person2_longitude: float = Form(0),
    person2_timezone: float = Form(0),
) -> HTMLResponse:
    form_values = {
        "chart_mode": chart_mode,
        "person_name": person_name,
        "birth_date": birth_date,
        "birth_time": birth_time,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "progressed_date": progressed_date,
        "progressed_time": progressed_time,
        "transit_date": transit_date,
        "transit_time": transit_time,
        "person2_name": person2_name,
        "person2_birth_date": person2_birth_date,
        "person2_birth_time": person2_birth_time,
        "person2_latitude": person2_latitude,
        "person2_longitude": person2_longitude,
        "person2_timezone": person2_timezone,
    }
    try:
        payload = _build_report(**form_values)
        return _render_page(request, form_values, report_payload=payload)
    except Exception as exc:
        logger.exception("Failed to generate report for mode=%s", chart_mode)
        return _render_page(request, form_values, error_message=str(exc))


async def _api_report(mode: str, **kwargs) -> JSONResponse:
    try:
        payload = _build_report(chart_mode=mode, **kwargs)
        return JSONResponse(
            {
                "mode": mode,
                "interpretation": payload["interpretation"],
                "result_text": payload.get("result_text", ""),
                "result_path": payload.get("result_path"),
                "interpretation_path": payload.get("interpretation_path"),
                "aspect_count": len(payload.get("aspects", [])),
            }
        )
    except Exception as exc:
        logger.exception("API report generation failed for mode=%s", mode)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/report/natal")
async def api_report_natal(
    person_name: str = Form("あなた"),
    birth_date: str = Form(...),
    birth_time: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    timezone: float = Form(...),
):
    return await _api_report(
        "natal",
        person_name=person_name,
        birth_date=birth_date,
        birth_time=birth_time,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
    )


@app.post("/api/report/progressed")
async def api_report_progressed(
    person_name: str = Form("あなた"),
    birth_date: str = Form(...),
    birth_time: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    timezone: float = Form(...),
    progressed_date: str = Form(...),
    progressed_time: str = Form("00:00"),
):
    return await _api_report(
        "progressed",
        person_name=person_name,
        birth_date=birth_date,
        birth_time=birth_time,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        progressed_date=progressed_date,
        progressed_time=progressed_time,
    )


@app.post("/api/report/transit")
async def api_report_transit(
    person_name: str = Form("あなた"),
    birth_date: str = Form(...),
    birth_time: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    timezone: float = Form(...),
    transit_date: str = Form(...),
    transit_time: str = Form("00:00"),
):
    return await _api_report(
        "transit",
        person_name=person_name,
        birth_date=birth_date,
        birth_time=birth_time,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        transit_date=transit_date,
        transit_time=transit_time,
    )


@app.post("/api/report/triple")
async def api_report_triple(
    person_name: str = Form("あなた"),
    birth_date: str = Form(...),
    birth_time: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    timezone: float = Form(...),
    progressed_date: str = Form(...),
    progressed_time: str = Form("00:00"),
    transit_date: str = Form(...),
    transit_time: str = Form("00:00"),
):
    return await _api_report(
        "triple",
        person_name=person_name,
        birth_date=birth_date,
        birth_time=birth_time,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        progressed_date=progressed_date,
        progressed_time=progressed_time,
        transit_date=transit_date,
        transit_time=transit_time,
    )


@app.post("/api/report/synastry")
async def api_report_synastry(
    person_name: str = Form("あなた"),
    birth_date: str = Form(...),
    birth_time: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    timezone: float = Form(...),
    person2_name: str = Form("相手"),
    person2_birth_date: str = Form(...),
    person2_birth_time: str = Form(...),
    person2_latitude: float = Form(...),
    person2_longitude: float = Form(...),
    person2_timezone: float = Form(...),
):
    return await _api_report(
        "synastry",
        person_name=person_name,
        birth_date=birth_date,
        birth_time=birth_time,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        person2_name=person2_name,
        person2_birth_date=person2_birth_date,
        person2_birth_time=person2_birth_time,
        person2_latitude=person2_latitude,
        person2_longitude=person2_longitude,
        person2_timezone=person2_timezone,
    )
