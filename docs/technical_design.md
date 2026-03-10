# 自販機型占星術サイト 技術設計（MVP）

## 1. 現状把握
- 既存 `astrology.py` に Swiss Ephemeris (`pyswisseph`) を使った占星術ロジックが実装済み。
- 主な再利用対象:
  - チャート計算 `calculate_astrology_data`
  - アスペクト計算 `calculate_aspects`
  - 複合アスペクト `calculate_composite_aspects`
  - 解釈テキスト生成 `generate_interpretation`
- 課題: notebook/CLI的な単一スクリプト構造でWeb APIからの再利用がしづらい。

## 2. 問題点
- 設定値がグローバルに散在し、APIごとの入出力境界が不明瞭。
- 永続化がテキストファイル前提で、結果ID管理がない。
- 入力バリデーションがUI/API経由を前提にしていない。
- エフェメリスパスが Colab 前提だったため、環境変数切替が必要。

## 3. 技術設計

### 3.1 全体アーキテクチャ
- `FastAPI` を入口にし、`service` 層で既存占星術関数を呼び出す。
- 結果は `data/results/*.json` として保存し、将来DBへ置換。
- テンプレートは `Jinja2` + `fetch` により軽量MVPを構築。

### 3.2 使用技術候補
- Backend: FastAPI, Uvicorn, Pydantic v2
- Astrology: pyswisseph (既存ロジック流用)
- Frontend: Jinja2 templates + vanilla JS
- Storage: JSON file (MVP), 将来 SQLite/PostgreSQL
- Infra: Docker / docker-compose

### 3.3 バックエンド構成
- `app/main.py`: 起動点、例外ハンドラ
- `app/api/routes.py`: API/画面ルーティング
- `app/services/astrology_service.py`: 占星術コア連携
- `app/schemas.py`: request/responseモデル
- `app/core/config.py`: 環境変数読み込み

### 3.4 フロントエンド構成
- ページ:
  - `/` トップ
  - `/form/natal` ネイタル入力
  - `/form/synastry` 相性診断入力
  - `/result/{id}/view` 結果表示
  - `/error` エラーページ
- `static/app.js` で API 呼び出し。

### 3.5 データフロー
1. ユーザーがフォーム入力。
2. JS から `/api/chart/*` へ POST。
3. Service 層で `astrology.py` の関数を呼び計算。
4. 結果JSONを `result_id` 付きで保存。
5. `/result/{id}` or `/result/{id}/view` で取得・表示。

### 3.6 将来の決済連携ポイント（技術のみ）
- `Order` テーブル（未実装）に `status=pending/paid/fulfilled` を保持。
- Webhook受信API（未実装）で `paid` 更新後、ジョブキューへ投入。
- `result_id` と `order_id` を紐付けて配信制御。

### 3.7 占い結果生成フロー
- Natal: 単独チャート生成。
- Synastry: 2チャート + 相互アスペクト + 複合アスペクト。
- Transit: natal/transit のクロスアスペクト。
- Report: `generate_interpretation` を直接呼び、テキスト返却。

### 3.8 エラーハンドリング方針
- ドメイン例外 `AstrologyError` を 4xx にマッピング。
- 想定外例外は API で 500 JSON、画面では `error.html`。
- バリデーションは Pydantic で事前防御。

### 3.9 ローカル開発方針
- `.env` で ephemeris path を切替。
- `uvicorn app.main:app --reload` で起動。
- まずファイル保存運用、DB導入は次段。

### 3.10 本番移行しやすい構成案
- Repository層を追加し JSON保存を RDB に置換。
- 非同期ワーカー（Celery/RQ）で計算ジョブ化。
- キャッシュ・再実行防止キー導入。

## 4. 占星術エンジンの切り出し方（提案）
既存ロジックを壊さず、`AstrologyService` でインターフェースを統一:
- `build_chart(birth_input)`
- `calculate_synastry(person1, person2)`
- `calculate_transit(natal, transit)`
- `generate_interpretation(person_name, chart, aspects, composites)`
- `export_result(payload)` / `load_result(result_id)`

## 5. API設計

### GET /health
- response: `{ "status": "ok" }`

### POST /api/chart/natal
- request:
```json
{
  "person_name": "あなた",
  "birth": {"date":"1984-11-15","time":"11:27","timezone":9,"lat":37.38,"lon":140.18}
}
```
- response: `{ result_id, chart, aspects, composite_aspects }`
- validation: date/time format, lat/lon range, timezone range
- errors: 422(validation), 400(domain)

### POST /api/chart/synastry
- request: `person1/person2` の BirthInput
- response: `{ result_id, chart, aspects, composite_aspects }`
- errors: 422, 400

### POST /api/chart/transit
- request: `natal` + `transit`
- response: `{ result_id, chart, aspects, composite_aspects:[] }`

### POST /api/report/render
- request: 計算済み `chart/aspects/composites`
- response: `{ "report_text": "..." }`

### GET /result/{id}
- response: `{ "id": "...", "payload": {...} }`
- errors: 404 when file missing

## 6. Web画面MVP
- トップページ: 導線
- ネイタルフォーム: 1人分入力
- 相性フォーム: 2人分入力
- 結果ページ: result JSON 表示
- エラーページ: メッセージ表示

## 7. 仮定（今回）
- 仮定1: ephemerisファイルは `./data/ephe` に配置可能。
- 仮定2: MVPではユーザー認証なし。
- 仮定3: 保存はJSONファイルで十分（将来DBへ移行）。
