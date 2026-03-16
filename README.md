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

## Quick auto setup/start scripts (かんたん起動 ✨)

このリポジトリには、セットアップ有無を自動判定して起動するスクリプトを追加しています。

### macOS / Linux

```bash
./start_auto.sh
```

### Windows (cmd.exe)

```bat
start_auto.bat
```

補足:

- 初回は `.venv` の作成と `requirements.txt` のインストールを自動実行
- 2回目以降は依存が揃っていればそのまま起動
- セットアップだけ実行する場合: `--setup-only`
- ホットリロード無効化: `--no-reload`
- venv 自動アクティベート対応（Windows は自動、macOS/Linux は `source start_auto.sh --setup-only` で現在シェルへ反映）

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

## 日本語補足（API・出力・注意点）

### Web API（日本語）

- `GET /`
- `GET /health`
- `POST /api/report`
- `POST /api/report/natal`
- `POST /api/report/progressed`
- `POST /api/report/transit`
- `POST /api/report/triple`
- `POST /api/report/synastry`

`/api/report` はHTMLページへ結果を再描画します。モード別APIは JSON で解釈文と保存先パスを返します。

### 出力ファイル（日本語）

生成ファイルは `data/results/` に保存されます。

- `astrology_result.txt`
- `astrology_interpretation.txt`

### 注意点（日本語）

- エフェメリスは `ASTROLOGY_EPHE_PATH` → `data/ephemeris` → `ephemeris` → `data/ephe` → `ephe` の順で自動検出されます。
- 有効な `.se1` ファイルが見つからない場合は、探索パス付きのエラーで起動に失敗します。



## USCS補助レイヤー（位相モデル）

このリポジトリは既存の占星術ロジック（天体計算・orb判定・通常解釈）を保持したまま、
**USCS的な位相補助レイヤー**を追加しています。

- 既存のアスペクト判定（orbベース）は main として維持
- phase/coherence/resonance は supplement として追加
- とくに `synastry` / `triple` で補助指標が有効

主な設定:

- `USE_USCS_PHASE`（または FastAPI 側は `ASTROLOGY_USE_USCS_PHASE`）
  - `true/1`: 位相補助指標をON
  - `false/0`: 従来挙動（orb中心）
- `USCS_VERBOSE`（または `ASTROLOGY_USCS_VERBOSE`）
  - 開発時の詳細表示フラグ

補助指標の表示名は一般向けに、
「同期度」「共鳴度」「集中度」など自然な表現を使っています。
