from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Astrology Local App")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "ok"}

# NOTE:
# Replace the body below with calls into astrology.py, for example:
# from astrology import run_report_by_mode, build_chart_from_input
# and dispatch based on chart_mode.

@app.post("/api/report", response_class=HTMLResponse)
async def report(
    request: Request,
    chart_mode: str = Form("natal"),
    person_name: str = Form("あなた"),
):
    demo_text = f"chart_mode={chart_mode} / person_name={person_name}\nここに占星レポートを表示します。"
    return templates.TemplateResponse("index.html", {"request": request, "report": demo_text, "chart_mode": chart_mode, "person_name": person_name})
