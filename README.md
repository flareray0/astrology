# astrology MVP (FastAPI)

## 1. 現状把握
このリポジトリは `astrology.py` に占星術エンジンが集約され、Swiss Ephemeris を使った以下が実装されています。
- ネイタル計算
- シナストリー
- トランジット
- メジャー / マイナーアスペクト
- 複合アスペクト検出
- テキスト保存
- 解釈レポート生成

今回のMVPでは、この既存ロジックを再利用し、FastAPI + HTMLフォームから実行できる最小Webアプリを追加しました。

## 2. 問題点
- 単一スクリプト構造で API 化されていない
- 結果取得のID管理がない
- 入力バリデーションが弱い
- ephemeris パスが環境に依存

## 3. 技術設計（概要）
詳細は [`docs/technical_design.md`](docs/technical_design.md) を参照してください。

- Backend: FastAPI / Pydantic
- Core: 既存 `astrology.py` を `app/services/astrology_service.py` から呼び出し
- Frontend: Jinja2 + fetch
- Storage: `data/results/*.json`
- Env: `.env` 経由で ephemeris パス切替

## 4. ディレクトリ構成案（今回反映済み）
```text
.
├─ app/
│  ├─ api/
│  ├─ core/
│  ├─ services/
│  ├─ main.py
│  └─ schemas.py
├─ templates/
├─ static/
├─ data/
│  └─ results/
├─ tests/
├─ scripts/
├─ docs/
├─ astrology.py
├─ Dockerfile
├─ docker-compose.yml
├─ .env.example
└─ README.md
```

## 5. API設計（MVP）

### GET /health
- response: `{"status":"ok"}`

### POST /api/chart/natal
```bash
curl -X POST http://localhost:8000/api/chart/natal \
  -H 'Content-Type: application/json' \
  -d '{
    "person_name":"あなた",
    "birth":{"date":"1984-11-15","time":"11:27","timezone":9,"lat":37.38,"lon":140.18}
  }'
```

### POST /api/chart/synastry
```bash
curl -X POST http://localhost:8000/api/chart/synastry \
  -H 'Content-Type: application/json' \
  -d '{
    "person1_name":"A","person2_name":"B",
    "person1":{"date":"1984-11-15","time":"11:27","timezone":9,"lat":37.38,"lon":140.18},
    "person2":{"date":"1967-05-13","time":"00:00","timezone":9,"lat":35.68,"lon":139.65}
  }'
```

### POST /api/chart/transit
```bash
curl -X POST http://localhost:8000/api/chart/transit \
  -H 'Content-Type: application/json' \
  -d '{
    "person_name":"あなた",
    "natal":{"date":"1984-11-15","time":"11:27","timezone":9,"lat":37.38,"lon":140.18},
    "transit":{"date":"2026-02-12","time":"00:00","timezone":9,"lat":37.38,"lon":140.18}
  }'
```

### POST /api/report/render
```bash
curl -X POST http://localhost:8000/api/report/render \
  -H 'Content-Type: application/json' \
  -d '{"person_name":"あなた","chart":[],"aspects":[],"composites":[]}'
```

### GET /result/{id}
```bash
curl http://localhost:8000/result/<result_id>
```

## 6. 実装コードのたたき台
- 起動: `app/main.py`
- ルーティング: `app/api/routes.py`
- スキーマ: `app/schemas.py`
- サービス: `app/services/astrology_service.py`
- テンプレート: `templates/*.html`
- 設定: `app/core/config.py`, `.env.example`
- Docker: `Dockerfile`, `docker-compose.yml`

## 7. 実行手順

### 必要パッケージ
- Python 3.11+
- `requirements.txt` のライブラリ

### ephemeris ファイルの置き場所
- デフォルト: `./data/ephe`
- 変更時: `.env` の `ASTROLOGY_EPHE_PATH` を更新

### ローカル起動方法
```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Docker起動
```bash
docker compose up --build
```

### ブラウザ確認
- `http://localhost:8000/`
- `http://localhost:8000/form/natal`
- `http://localhost:8000/form/synastry`

## 8. 残課題 / 次ステップ

### 今回実装済み
- FastAPI API
- HTML入力フォーム
- 結果JSON保存
- 解釈レポートAPI
- Docker/環境変数対応

### 次にやるべきこと
- SQLite repository層追加
- `/api/report/render` のテンプレート選択式
- 結果HTMLレンダリング整備
- 単体テスト拡充

### 本番前に必要なこと
- PostgreSQL移行
- 非同期ジョブ化（計算キュー）
- 監視・ログ・リトライ
- 決済Webhook連携（技術実装のみ）
