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

## 日本語での使い方 (。・ω・。)

### 1) セットアップ

```bash
git clone <repo>
cd astrology
pip install -r requirements.txt
```

### 2) Webアプリ起動

```bash
uvicorn web.app:app --reload
```

ブラウザで `http://127.0.0.1:8000` を開き、フォームに以下を入力します。

- チャートモード（`natal / progressed / transit / triple / synastry`）
- 生年月日
- 出生時刻
- 緯度・経度
- タイムゾーン
- （シナストリー時）2人目の情報

「Generate report」を押すと、画面下に解釈テキストが表示されます。

### 3) CLI実行（ターミナル）

```bash
python astrology.py
```

対話形式で入力してレポートを生成します。既定値で実行する場合:

```bash
python astrology.py --non-interactive
```

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

- Repository audit and missing-piece summary: [docs/repo_audit.md](docs/repo_audit.md)
- Primary web entry point: [web/app.py](web/app.py)
- Main chart/report engine: [astrology.py](astrology.py)
