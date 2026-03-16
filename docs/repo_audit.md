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

## Missing pieces identified before implementation
- Needed robust validation for synastry second-person fields in the web request path.
- Needed consistent API `aspect_count` semantics for `triple` mode (nested aspect sets).
- Needed a deterministic local test invocation path so imports resolve in this repo layout.

## Implemented in this pass
- Added strict synastry input validation in `web/app.py` to fail fast with a clear error for blank second-person date/time.
- Added `_aspect_count(...)` helper in `web/app.py` so `/api/report/*` returns a true aggregate count for both flat and nested aspect payloads.
- Added `pytest.ini` with `pythonpath = .` so local test execution works from a clean clone without manual `PYTHONPATH` export.
