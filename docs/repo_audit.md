# Repository Audit

## Required files reviewed
- `astrology.py`
- `AGENT.md`
- `CODEX_NOTES.md`
- `web/app.py`
- `README.md`

## Existing engine pieces found
- Chart calculation: `calculate_astrology_data(...)`, `build_chart_from_input(...)`
- Aspect calculation: `calculate_aspects(...)`, `calculate_composite_aspects(...)`
- Report generation: `generate_natal_interpretation(...)`, `generate_progressed_interpretation(...)`, `generate_transit_interpretation(...)`, `generate_triple_interpretation(...)`, `generate_synastry_interpretation(...)`, `run_report_by_mode(...)`
- Aspect meaning layer: `aspect_engine.interpret_aspect(...)`

## Missing or incomplete pieces before implementation
- `web/app.py` was a stub and did not call the astrology engine.
- `web/templates/index.html` only supported mode and name, with no birth data fields or synastry input.
- Mode-specific API endpoints were missing.
- Output files defaulted to repo root instead of `data/results/`.
- CLI flow depended on hard-coded constants instead of a usable interactive run path.
- Interpretation helper functions requested by spec were not exposed with stable names:
  - `interpret_planet_position()`
  - `interpret_house_overlay()`
  - `synthesize_interpretation()`
- Ephemeris detection existed, but its search order did not match the required order exactly.

## Implementation direction
- Keep the existing chart and report engine.
- Add thin interpretation wrappers rather than replacing the working narrative generator.
- Make `uvicorn web.app:app --reload` the primary supported run target.
- Persist both structured summary and narrative interpretation under `data/results/`.
