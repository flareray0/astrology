import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Astrology Vending MVP"
    env: str = "local"
    debug: bool = True

    astrology_ephe_path: str = "./data/ephe"
    astrology_house_system: str = "K"
    include_asteroids: bool = True
    include_minor_aspects: bool = True

    data_dir: Path = Path("data")
    results_dir: Path = Path("data/results")

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ASTROLOGY_", extra="ignore")


settings = Settings()

if os.getenv("RESULT_OUTPUT_DIR"):
    settings.results_dir = Path(os.getenv("RESULT_OUTPUT_DIR", "data/results"))

settings.results_dir.mkdir(parents=True, exist_ok=True)
