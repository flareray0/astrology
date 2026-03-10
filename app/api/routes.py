from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.exceptions import AstrologyError
from app.schemas import (
    ChartResponse,
    NatalChartRequest,
    ProgressedRequest,
    ReportRenderRequest,
    ReportRenderResponse,
    ResultResponse,
    SynastryRequest,
    TransitRequest,
    TripleRequest,
)
from app.services.astrology_service import astrology_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/api/chart/natal", response_model=ChartResponse)
def natal_chart(req: NatalChartRequest) -> ChartResponse:
    try:
        chart, _ = astrology_service.build_chart(req.birth)
        aspects = []
        payload = {"type": "natal", "person_name": req.person_name, "chart": chart, "aspects": aspects, "composite_aspects": []}
        result_id = astrology_service.export_result(payload)
        return ChartResponse(result_id=result_id, chart=chart, aspects=aspects, composite_aspects=[])
    except AstrologyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/api/chart/synastry", response_model=ChartResponse)
def synastry_chart(req: SynastryRequest) -> ChartResponse:
    try:
        result = astrology_service.calculate_synastry(req.person1, req.person2)
        payload = {"type": "synastry", "person1_name": req.person1_name, "person2_name": req.person2_name, **result}
        result_id = astrology_service.export_result(payload)
        return ChartResponse(result_id=result_id, **result)
    except AstrologyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/api/chart/transit", response_model=ChartResponse)
def transit_chart(req: TransitRequest) -> ChartResponse:
    try:
        result = astrology_service.calculate_transit(req.natal, req.transit)
        payload = {"type": "transit", "person_name": req.person_name, **result}
        result_id = astrology_service.export_result(payload)
        return ChartResponse(result_id=result_id, chart=result["chart"], aspects=result["aspects"], composite_aspects=result["composite_aspects"])
    except AstrologyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/api/chart/progressed", response_model=ChartResponse)
def progressed_chart(req: ProgressedRequest) -> ChartResponse:
    try:
        result = astrology_service.calculate_progressed(req.natal, req.progressed)
        payload = {"type": "progressed", "person_name": req.person_name, **result}
        result_id = astrology_service.export_result(payload)
        return ChartResponse(result_id=result_id, chart=result["chart"], aspects=result["aspects"], composite_aspects=result["composite_aspects"])
    except AstrologyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/api/chart/triple", response_model=ChartResponse)
def triple_chart(req: TripleRequest) -> ChartResponse:
    try:
        result = astrology_service.calculate_triple(req.natal, req.progressed, req.transit)
        payload = {"type": "triple", "person_name": req.person_name, **result}
        result_id = astrology_service.export_result(payload)
        return ChartResponse(result_id=result_id, chart=result["chart"], aspects=result["aspects"], composite_aspects=result["composite_aspects"])
    except AstrologyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/api/report/render", response_model=ReportRenderResponse)
def render_report(req: ReportRenderRequest) -> ReportRenderResponse:
    report = astrology_service.generate_interpretation(req.person_name, req.chart, req.aspects, req.composites, req.chart_mode, req.context)
    return ReportRenderResponse(report_text=report)


@router.get("/result/{result_id}", response_model=ResultResponse)
def get_result(result_id: str) -> ResultResponse:
    try:
        payload = astrology_service.load_result(result_id)
        return ResultResponse(id=result_id, payload=payload)
    except AstrologyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/", response_class=HTMLResponse)
def top_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/form/natal", response_class=HTMLResponse)
def natal_form(request: Request):
    return templates.TemplateResponse("natal_form.html", {"request": request})


@router.get("/form/synastry", response_class=HTMLResponse)
def synastry_form(request: Request):
    return templates.TemplateResponse("synastry_form.html", {"request": request})


@router.get("/result/{result_id}/view", response_class=HTMLResponse)
def result_view(request: Request, result_id: str):
    payload = astrology_service.load_result(result_id)
    return templates.TemplateResponse("result.html", {"request": request, "result_id": result_id, "payload": payload})
