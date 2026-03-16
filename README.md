# Astrology Local App Scaffold

このリポジトリは、占星術エンジンをローカルで起動し、`localhost` から試せる状態まで持っていくための土台です。

## 目的
- `git clone` 後にローカル起動できる
- Swiss Ephemeris (`.se1`) を repo 内から自動検出できる
- Natal / Progressed / Transit / Triple / Synastry を扱える
- FastAPI + HTML フォームでブラウザから試せる

## 推奨ディレクトリ構成
```text
astrology/
├─ astrology.py
├─ aspect_engine.py
├─ interpretation_engine.py
├─ report_engine.py
├─ web/
│  ├─ app.py
│  ├─ templates/
│  │  └─ index.html
│  └─ static/
├─ data/
│  ├─ ephemeris/
│  │  ├─ *.se1
│  └─ results/
├─ requirements.txt
├─ Dockerfile
├─ docker-compose.yml
├─ .env.example
└─ README.md
```

## クイックスタート（ローカル）
### Windows PowerShell
```powershell
git clone <YOUR_REPO_URL>
cd astrology
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn web.app:app --reload
```

### Linux / macOS
```bash
git clone <YOUR_REPO_URL>
cd astrology
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn web.app:app --reload
```

ブラウザ:
```text
http://127.0.0.1:8000
```

## Colab から試す
private repo の場合は token を使って clone してください。
```python
import getpass, os
token = getpass.getpass("GitHub Token: ")
!git clone https://{token}@github.com/<USER>/<REPO>.git
%cd <REPO>
!pip install -r requirements.txt
```

## Ephemeris
デフォルトでは以下を順番に探索:
- `ASTROLOGY_EPHE_PATH`
- `data/ephemeris/`
- `ephemeris/`
- `data/ephe/`
- `ephe/`

## API 方針
最低限以下のエンドポイントを推奨:
- `POST /api/report/natal`
- `POST /api/report/progressed`
- `POST /api/report/transit`
- `POST /api/report/triple`
- `POST /api/report/synastry`

## Web UI 方針
1ページで:
- chart mode 選択
- 1人分 / 2人分入力
- 結果表示
- txt 保存ダウンロード

## 実装優先順位
1. ephemeris 自動検出
2. FastAPI 起動
3. natal レポート
4. synastry レポート
5. progressed / transit / triple
6. 出力品質強化
