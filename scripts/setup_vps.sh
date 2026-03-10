#!/usr/bin/env bash
set -euo pipefail

# Clone直後に最小構成でローカル検証を開始するためのセットアップスクリプト
# Usage:
#   bash scripts/setup_vps.sh
# Optional env vars:
#   PYTHON_BIN=python3.11 VENV_DIR=.venv APP_HOST=0.0.0.0 APP_PORT=8000 bash scripts/setup_vps.sh

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"
APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-8000}"

log() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$1"
}

log "Python 実行ファイル確認: ${PYTHON_BIN}"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "ERROR: ${PYTHON_BIN} が見つかりません。PYTHON_BIN を指定してください。" >&2
  exit 1
fi
"${PYTHON_BIN}" --version

log "仮想環境作成: ${VENV_DIR}"
if [ ! -d "${VENV_DIR}" ]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

log "依存インストール"
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

log ".env 準備"
if [ ! -f .env ]; then
  cp .env.example .env
fi

log "必要ディレクトリ作成"
mkdir -p data/ephe data/results

log "最小 import チェック"
python - <<'PY'
import importlib
modules = ["fastapi", "uvicorn", "jinja2", "pydantic", "pydantic_settings"]
for module in modules:
    importlib.import_module(module)
print("import check: ok")
PY

cat <<MSG

✅ setup 完了

次の手順:
  source ${VENV_DIR}/bin/activate
  uvicorn app.main:app --host ${APP_HOST} --port ${APP_PORT} --reload

疎通確認:
  curl -sS http://127.0.0.1:${APP_PORT}/health
  curl -I http://127.0.0.1:${APP_PORT}/form/natal

補足:
- ephemeris は data/ephe に配置（必要に応じて .env の ASTROLOGY_EPHE_PATH を変更）
MSG
