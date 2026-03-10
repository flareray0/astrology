import json
import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import swisseph as swe

from app.core.config import settings
from app.core.exceptions import AstrologyError
from app.schemas import BirthInput

import astrology


class AstrologyService:
    def __init__(self) -> None:
        swe.set_ephe_path(settings.astrology_ephe_path)
        os.environ["ASTROLOGY_EPHE_PATH"] = settings.astrology_ephe_path

    @staticmethod
    def _to_chart_seed(birth: BirthInput) -> dict:
        ut_hour = astrology.convert_time_to_ut_decimal_hours(birth.time, birth.timezone)
        return {
            "julian_day": swe.julday(birth.date.year, birth.date.month, birth.date.day, ut_hour),
            "lat": birth.lat,
            "lon": birth.lon,
        }

    def build_chart(self, birth: BirthInput) -> tuple[list[dict], list[float]]:
        seed = self._to_chart_seed(birth)
        chart, cusps = astrology.calculate_astrology_data(
            seed["julian_day"],
            seed["lat"],
            seed["lon"],
            hsys=settings.astrology_house_system,
            include_asteroids=settings.include_asteroids,
        )
        if not chart:
            raise AstrologyError("Failed to compute astrology chart")
        return chart, cusps

    def calculate_synastry(self, person1: BirthInput, person2: BirthInput) -> dict:
        chart1, _ = self.build_chart(person1)
        chart2, _ = self.build_chart(person2)
        aspects = astrology.calculate_aspects(chart1, chart2, settings.include_minor_aspects)
        composites = astrology.calculate_composite_aspects(chart1 + chart2, astrology.COMPOSITE_ASPECTS)
        return {"chart": chart1 + chart2, "aspects": aspects, "composite_aspects": composites}

    def calculate_transit(self, natal: BirthInput, transit: BirthInput) -> dict:
        natal_chart, _ = self.build_chart(natal)
        transit_chart, _ = self.build_chart(transit)
        aspects = astrology.calculate_aspects(natal_chart, transit_chart, settings.include_minor_aspects)
        return {"chart": natal_chart + transit_chart, "aspects": aspects, "composite_aspects": []}

    def generate_interpretation(self, person_name: str, chart: list[dict], aspects: list[dict], composites: list[dict]) -> str:
        return astrology.generate_interpretation(
            natal_chart=chart,
            aspects_sets=[(aspects, "自動生成アスペクト")],
            composite_sets=[(composites, "自動生成複合アスペクト")],
            person_name=person_name,
        )

    def export_result(self, payload: dict) -> str:
        result_id = f"res_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"
        output_path = Path(settings.results_dir) / f"{result_id}.json"
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return result_id

    def load_result(self, result_id: str) -> dict:
        path = Path(settings.results_dir) / f"{result_id}.json"
        if not path.exists():
            raise AstrologyError(f"Result not found: {result_id}")
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)


astrology_service = AstrologyService()
