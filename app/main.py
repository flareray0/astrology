from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import router
from app.core.config import settings
from app.core.exceptions import AstrologyError

app = FastAPI(title=settings.app_name, debug=settings.debug)
app.include_router(router)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.exception_handler(AstrologyError)
async def astrology_error_handler(_: Request, exc: AstrologyError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=500, content={"detail": "internal server error"})
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "message": str(exc)},
        status_code=500,
    )


@app.get("/error", response_class=HTMLResponse)
def error_page(request: Request):
    return templates.TemplateResponse("error.html", {"request": request, "message": "エラーが発生しました。"})
