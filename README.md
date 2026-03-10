# astrology MVP (FastAPI)

この README は **「まずローカルで FastAPI MVP が起動し、主要エンドポイントが疎通するか」** を最優先にした最小手順です。

## 0. 前提
- Python 3.11+
- `pip` が利用可能
- このリポジトリ直下で作業

---

## 1. 依存関係の確認

```bash
python --version
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` は以下を前提としています（FastAPI/uvicorn/Jinja2/Pydantic/Swiss Ephemeris）。

---

## 2. ephemeris 配置前提の確認

本アプリは `ASTROLOGY_EPHE_PATH`（既定値: `./data/ephe`）を Swiss Ephemeris の参照先に使います。

```bash
cp .env.example .env
mkdir -p data/ephe data/results
```

- 既定値のまま使う場合は `data/ephe` に ephemeris ファイルを配置
- 変更する場合は `.env` の `ASTROLOGY_EPHE_PATH` を実パスへ更新
- 小惑星（Eros/Persephone）計算に必要なデータが不足している場合、該当天体はスキップされる可能性があります

---

## 3. ローカル起動手順（最小）

初回 clone 直後にまとめて準備する場合（推奨）:

```bash
bash scripts/setup_vps.sh
```

手動で行う場合:

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

または:

```bash
source .venv/bin/activate
bash scripts/run_local.sh
```

---

## 4. `/health` の疎通確認

別ターミナルで:

```bash
curl -sS http://127.0.0.1:8000/health
```

期待値:

```json
{"status":"ok"}
```

---

## 5. `/form/natal` の画面確認

ブラウザで以下を開く:

- `http://127.0.0.1:8000/form/natal`

CLI で最低限確認する場合:

```bash
curl -I http://127.0.0.1:8000/form/natal
```

`HTTP/1.1 200 OK` なら到達できています。

---

## 6. `/api/chart/natal` のサンプルリクエスト確認

```bash
curl -sS -X POST http://127.0.0.1:8000/api/chart/natal \
  -H 'Content-Type: application/json' \
  -d '{
    "person_name": "あなた",
    "birth": {
      "date": "1984-11-15",
      "time": "11:27",
      "timezone": 9,
      "lat": 37.38,
      "lon": 140.18
    }
  }'
```

期待値:
- HTTP 200
- `result_id`, `chart`, `aspects`, `composite_aspects` を含む JSON

---

## 7. 起動時に詰まりやすい箇所（先回りチェック）

1. **依存パッケージ未導入**
   - 症状: `ModuleNotFoundError: fastapi` など
   - 対応: 仮想環境を有効化して `pip install -r requirements.txt` を再実行

2. **ephemeris パス不整合**
   - 症状: 計算結果が不完全、または天体計算エラー
   - 対応: `.env` の `ASTROLOGY_EPHE_PATH` と実ファイル配置先を一致させる

3. **ポート競合（8000）**
   - 症状: `Address already in use`
   - 対応: 別ポート起動（例: `--port 8001`）

4. **入力フォーマット不正（特に `time`）**
   - 症状: 422 Unprocessable Entity
   - 対応: `time` は必ず `HH:MM`（24時間表記）

5. **`data/results` 未作成時の書き込み失敗**
   - 対応: `mkdir -p data/results`（通常は起動時に自動生成されますが、先に作成しておくと安全）

---

## 8. 補足（MVP の確認対象）

- ヘルスチェック: `GET /health`
- 入力画面: `GET /form/natal`, `GET /form/synastry`
- API: `POST /api/chart/natal`, `POST /api/chart/synastry`, `POST /api/chart/transit`
- 結果参照: `GET /result/{result_id}`, `GET /result/{result_id}/view`

「まず動くか確認する」目的では、**`/health` → `/form/natal` → `/api/chart/natal`** の順で確認するのが最短です。
