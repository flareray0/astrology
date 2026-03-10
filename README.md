# astrology

`astrology.py` を正本ロジックとして、Colab / Windows / Linux で同じ導線で検証・実行できるように整備したリポジトリです。

## 1. 現状の環境依存問題（整理）

- ephemeris 参照先が固定パスだと clone 先の違いで壊れる
- Notebook と `.py` で実行導線が分かれると検証の再現性が落ちる
- カレントディレクトリ依存の出力は環境差で行方不明になりやすい
- clone 後の最短動作確認コマンドが不明瞭だと初期離脱が増える

## 2. 改修方針

- **DiffOnly原則**: 占星術ロジックは維持し、環境吸収レイヤーを追加
- ephemeris は `ASTROLOGY_EPHE_PATH` 優先、未指定時は repo 相対候補を探索
- レポート出力先は `RESULT_OUTPUT_DIR` で環境差を吸収
- Notebook は `astrology.py` を import して実行（UI/補助用途へ寄せる）
- clone 直後に使える `scripts/` のサンプル実行導線を追加

---

## 3. セットアップ（共通）

```bash
git clone <your-fork-or-origin-url>
cd astrology
cp .env.example .env
```

> ephemeris ファイルを `data/ephe` に配置するか、`ASTROLOGY_EPHE_PATH` で既存配置先を指定してください。

---


## 3.1 ephemeris ディレクトリ構成（se1配置）

se1 ファイルをアップロード済みの場合は、まず以下に集約してください。

```bash
python scripts/organize_ephe.py
# 既存ファイルを残したい場合
python scripts/organize_ephe.py --copy
```

推奨構成:

```text
astrology/
  data/
    ephe/      # .se1/.se2/.sef
    results/   # 実行結果
```

`data/ephe` が `ASTROLOGY_EPHE_PATH` のデフォルト探索先です。

---

## 4. Colab での使い方

`astrology.ipynb` は以下の5ステップ構成です。

1. clone / pull + `pip install -r requirements.txt`
2. `import astrology` + `reload`
3. 入力設定（chart_mode, 日時, 緯度経度）
4. `run_report_by_mode(...)` 実行
5. 生成ファイルをダウンロード

Notebook 内で環境変数を自動設定します。

- `ASTROLOGY_EPHE_PATH=/content/astrology/data/ephe`
- `RESULT_OUTPUT_DIR=/content/astrology/data/results`

---

## 5. Windows での使い方

```powershell
git clone <your-fork-or-origin-url>
cd astrology
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

動作確認（まずこれ）:

```powershell
python scripts/run_natal_example.py
python scripts/run_synastry_example.py
```

FastAPI 起動:

```powershell
python scripts/run_fastapi_dev.py
```

Notebook 起動:

```powershell
jupyter lab
```

---

## 6. Linux での使い方

```bash
git clone <your-fork-or-origin-url>
cd astrology
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

動作確認（まずこれ）:

```bash
python scripts/run_natal_example.py
python scripts/run_synastry_example.py
```

FastAPI 起動:

```bash
python scripts/run_fastapi_dev.py
# or
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Notebook 起動:

```bash
jupyter lab
```

---

## 7. FastAPI 起動とAPI確認

起動後:

- Health: `GET http://127.0.0.1:8000/health`
- 入力フォーム: `GET /form/natal`, `GET /form/synastry`
- API: `POST /api/chart/natal|progressed|transit|triple|synastry`

最小確認例:

```bash
curl -sS http://127.0.0.1:8000/health
```

---

## 8. chart_mode の違い

- `natal`: 出生図
- `progressed`: 二次進行（出生 + 基準時）
- `transit`: トランジット（出生 + 現在時）
- `triple`: natal + progressed + transit 統合
- `synastry`: 2人相性

共通導線として `astrology.run_report_by_mode(...)` を使えます。

---

## 9. ephemeris path の設定方法

優先順位:

1. `ASTROLOGY_EPHE_PATH`（環境変数）
2. repo 相対候補（`data/ephe`, `ephe` など）

例（Linux/macOS）:

```bash
export ASTROLOGY_EPHE_PATH="$(pwd)/data/ephe"
```

例（Windows PowerShell）:

```powershell
$env:ASTROLOGY_EPHE_PATH = "$(Get-Location)\data\ephe"
```

---

## 10. .env / 環境変数

`.env.example` の主要項目:

- `ASTROLOGY_EPHE_PATH`: ephemeris データ参照先
- `RESULT_OUTPUT_DIR`: 生成レポート出力先
- `APP_ENV`: 実行環境ラベル
- `CHART_MODE_DEFAULT`: デフォルトチャートモード
- `ASTROLOGY_HOUSE_SYSTEM`, `ASTROLOGY_INCLUDE_ASTEROIDS`, `ASTROLOGY_INCLUDE_MINOR_ASPECTS`

---

## 11. clone 後の最小確認手順（チェックリスト）

- [ ] `python -c "import astrology; print(astrology.EPHEMERIS_PATH)"` が通る
- [ ] `python scripts/run_natal_example.py` で natal レポート出力
- [ ] `python scripts/run_synastry_example.py` で synastry レポート出力
- [ ] `python scripts/run_fastapi_dev.py` で API 起動
- [ ] `curl http://127.0.0.1:8000/health` が `{"status":"ok"}` を返す
- [ ] Notebook から `run_report_by_mode(...)` 実行できる

---

## 12. 公開関数（Notebook/スクリプト向け）

- `build_chart_from_input(...)`
- `run_natal_report(...)`
- `run_progressed_report(...)`
- `run_transit_report(...)`
- `run_triple_report(...)`
- `run_synastry_report(...)`
- `run_report_by_mode(...)` ← モード分岐を統一
- `configure_ephemeris_path(...)`

返り値には `chart`, `aspects`, `composites`, `interpretation`, `result_path`, `interpretation_path` が含まれます。
