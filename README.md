# Astrology Local App

Local astrology application with Swiss Ephemeris chart calculation, interpretation generation, CLI support, and a FastAPI web UI.

## Run locally

```bash
git clone <repo>
cd astrology
pip install -r requirements.txt
uvicorn web.app:app --reload
```

Open `http://127.0.0.1:8000`.

## Supported chart modes

- `natal`
- `progressed`
- `transit`
- `triple`
- `synastry`

## Ephemeris handling

Swiss Ephemeris is auto-detected in this order:

1. `ASTROLOGY_EPHE_PATH`
2. `data/ephemeris`
3. `ephemeris`
4. `data/ephe`
5. `ephe`

If no valid `.se1` files are found, startup fails with a clear error listing the searched paths.

## Web API

- `GET /`
- `GET /health`
- `POST /api/report`
- `POST /api/report/natal`
- `POST /api/report/progressed`
- `POST /api/report/transit`
- `POST /api/report/triple`
- `POST /api/report/synastry`

`/api/report` renders the HTML page with the generated report. The mode-specific endpoints return JSON payloads containing interpretation text and saved file paths.

## Output files

Generated files are written to `data/results/`:

- `astrology_result.txt`
- `astrology_interpretation.txt`

## CLI

Interactive mode:

```bash
python astrology.py
```

Non-interactive defaults:

```bash
python astrology.py --non-interactive
```

The CLI prints the report and saves both output files under `data/results/`.

## Notes

- Repository audit and missing-piece summary: [docs/repo_audit.md](/H:/astrology/docs/repo_audit.md)
- Primary web entry point: [web/app.py](/H:/astrology/web/app.py)
- Main chart/report engine: [astrology.py](/H:/astrology/astrology.py)
