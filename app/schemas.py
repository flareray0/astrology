from datetime import date
from pydantic import BaseModel, Field, field_validator


class BirthInput(BaseModel):
    date: date
    time: str = Field(..., examples=["11:27"])
    timezone: int = Field(..., ge=-12, le=14)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)

    @field_validator("time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        if len(value) != 5 or value[2] != ":":
            raise ValueError("time must be HH:MM")
        hh, mm = value.split(":")
        if not (hh.isdigit() and mm.isdigit()):
            raise ValueError("time must be HH:MM")
        if not (0 <= int(hh) <= 23 and 0 <= int(mm) <= 59):
            raise ValueError("time must be HH:MM")
        return value


class NatalChartRequest(BaseModel):
    person_name: str = "あなた"
    birth: BirthInput


class SynastryRequest(BaseModel):
    person1_name: str = "Person A"
    person2_name: str = "Person B"
    person1: BirthInput
    person2: BirthInput


class TransitRequest(BaseModel):
    person_name: str = "あなた"
    natal: BirthInput
    transit: BirthInput


class ProgressedRequest(BaseModel):
    person_name: str = "あなた"
    natal: BirthInput
    progressed: BirthInput


class TripleRequest(BaseModel):
    person_name: str = "あなた"
    natal: BirthInput
    progressed: BirthInput
    transit: BirthInput


class ReportRenderRequest(BaseModel):
    person_name: str = "あなた"
    chart_mode: str = "natal"
    chart: list[dict]
    aspects: list[dict]
    composites: list[dict] = []
    context: dict = {}


class ChartResponse(BaseModel):
    result_id: str
    chart: list[dict]
    aspects: list[dict]
    composite_aspects: list[dict] = []


class ReportRenderResponse(BaseModel):
    report_text: str


class ResultResponse(BaseModel):
    id: str
    payload: dict
