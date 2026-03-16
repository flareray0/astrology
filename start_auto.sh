#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

VENV_DIR="${VENV_DIR:-.venv}"
HOST="${APP_HOST:-127.0.0.1}"
PORT="${APP_PORT:-8000}"
SETUP_ONLY=0
RELOAD_FLAG="--reload"
IS_SOURCED=0
if [ "${BASH_SOURCE[0]}" != "$0" ]; then
  IS_SOURCED=1
fi

for arg in "$@"; do
  case "${arg}" in
    --setup-only)
      SETUP_ONLY=1
      ;;
    --no-reload)
      RELOAD_FLAG=""
      ;;
  esac
done

log() {
  printf '[auto-launch] %s\n' "$1"
}

activate_venv_if_possible() {
  if [ "${IS_SOURCED}" -eq 1 ]; then
    # shellcheck disable=SC1090
    source "${ROOT_DIR}/${VENV_DIR}/bin/activate"
    log "venvを自動アクティベートしました ✅"
  else
    log "補足: venvを現在のシェルへ反映するには 'source start_auto.sh --setup-only' を使ってね"
  fi
}

pick_python() {
  if [ -x "${ROOT_DIR}/${VENV_DIR}/bin/python" ]; then
    echo "${ROOT_DIR}/${VENV_DIR}/bin/python"
    return
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi

  if command -v python >/dev/null 2>&1; then
    command -v python
    return
  fi

  echo ""
}

PYTHON_BIN="$(pick_python)"
if [ -z "${PYTHON_BIN}" ]; then
  echo "ERROR: Python が見つかりません。Python 3.10+ をインストールしてください。" >&2
  exit 1
fi

log "Python: ${PYTHON_BIN}"
"${PYTHON_BIN}" --version

setup_needed=0
if [ ! -d "${ROOT_DIR}/${VENV_DIR}" ]; then
  log "仮想環境がないので作成します: ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${ROOT_DIR}/${VENV_DIR}"
  setup_needed=1
fi

VENV_PYTHON="${ROOT_DIR}/${VENV_DIR}/bin/python"
VENV_PIP="${ROOT_DIR}/${VENV_DIR}/bin/pip"

if ! "${VENV_PYTHON}" -c "import fastapi, uvicorn, jinja2" >/dev/null 2>&1; then
  log "依存関係が未セットアップなのでインストールします ✨"
  setup_needed=1
fi

if [ "${setup_needed}" -eq 1 ]; then
  "${VENV_PIP}" install --upgrade pip
  "${VENV_PIP}" install -r requirements.txt
else
  log "依存関係はすでにOKです ✅"
fi

activate_venv_if_possible

if [ "${SETUP_ONLY}" -eq 1 ]; then
  log "--setup-only が指定されたため、ここで終了します。"
  if [ "${IS_SOURCED}" -eq 1 ]; then
    return 0
  fi
  exit 0
fi

APP_TARGET=""
if [ -f "${ROOT_DIR}/web/app.py" ]; then
  APP_TARGET="web.app:app"
elif [ -f "${ROOT_DIR}/app/main.py" ]; then
  APP_TARGET="app.main:app"
else
  echo "ERROR: 起動対象が見つかりません (web/app.py または app/main.py)。" >&2
  exit 1
fi

log "起動ターゲット: ${APP_TARGET}"
log "ブラウザで http://${HOST}:${PORT} を開いてね (。・ω・。)"

if [ -n "${RELOAD_FLAG}" ]; then
  if [ "${IS_SOURCED}" -eq 1 ]; then
    uvicorn "${APP_TARGET}" --host "${HOST}" --port "${PORT}" ${RELOAD_FLAG}
  else
    exec "${ROOT_DIR}/${VENV_DIR}/bin/uvicorn" "${APP_TARGET}" --host "${HOST}" --port "${PORT}" ${RELOAD_FLAG}
  fi
else
  if [ "${IS_SOURCED}" -eq 1 ]; then
    uvicorn "${APP_TARGET}" --host "${HOST}" --port "${PORT}"
  else
    exec "${ROOT_DIR}/${VENV_DIR}/bin/uvicorn" "${APP_TARGET}" --host "${HOST}" --port "${PORT}"
  fi
fi
