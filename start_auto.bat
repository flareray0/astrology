@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

if "%VENV_DIR%"=="" set "VENV_DIR=.venv"
if "%APP_HOST%"=="" set "APP_HOST=127.0.0.1"
if "%APP_PORT%"=="" set "APP_PORT=8000"
set "SETUP_ONLY=0"
set "RELOAD_FLAG=--reload"

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--setup-only" set "SETUP_ONLY=1"
if /I "%~1"=="--no-reload" set "RELOAD_FLAG="
shift
goto parse_args

:args_done
set "PYTHON_BIN="
if exist "%VENV_DIR%\Scripts\python.exe" (
  set "PYTHON_BIN=%VENV_DIR%\Scripts\python.exe"
) else (
  where py >nul 2>nul && set "PYTHON_BIN=py"
  if "!PYTHON_BIN!"=="" where python >nul 2>nul && set "PYTHON_BIN=python"
)

if "%PYTHON_BIN%"=="" (
  echo [auto-launch] ERROR: Python ^(3.10+^) が見つかりません。
  exit /b 1
)

echo [auto-launch] Python: %PYTHON_BIN%
%PYTHON_BIN% --version

set "SETUP_NEEDED=0"
if not exist "%VENV_DIR%\Scripts\python.exe" (
  echo [auto-launch] 仮想環境を作成します: %VENV_DIR%
  %PYTHON_BIN% -m venv "%VENV_DIR%"
  if errorlevel 1 exit /b 1
  set "SETUP_NEEDED=1"
)

"%VENV_DIR%\Scripts\python.exe" -c "import fastapi, uvicorn, jinja2" >nul 2>nul
if errorlevel 1 (
  echo [auto-launch] 依存関係をインストールします ✨
  set "SETUP_NEEDED=1"
)

if "%SETUP_NEEDED%"=="1" (
  "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
  if errorlevel 1 exit /b 1
  "%VENV_DIR%\Scripts\pip.exe" install -r requirements.txt
  if errorlevel 1 exit /b 1
) else (
  echo [auto-launch] 依存関係はすでにOKです ✅
)

if "%SETUP_ONLY%"=="1" (
  call "%VENV_DIR%\Scripts\activate.bat"
  echo [auto-launch] venvを自動アクティベートしました ✅
  echo [auto-launch] --setup-only 指定なので終了します。
  exit /b 0
)

set "APP_TARGET="
if exist "web\app.py" (
  set "APP_TARGET=web.app:app"
) else if exist "app\main.py" (
  set "APP_TARGET=app.main:app"
)

if "%APP_TARGET%"=="" (
  echo [auto-launch] ERROR: 起動対象が見つかりません ^(web\app.py or app\main.py^).
  exit /b 1
)

echo [auto-launch] 起動ターゲット: %APP_TARGET%
echo [auto-launch] ブラウザで http://%APP_HOST%:%APP_PORT% を開いてね (。・ω・。)
call "%VENV_DIR%\Scripts\activate.bat"
echo [auto-launch] venvを自動アクティベートしました ✅

if "%RELOAD_FLAG%"=="" (
  uvicorn %APP_TARGET% --host %APP_HOST% --port %APP_PORT%
) else (
  uvicorn %APP_TARGET% --host %APP_HOST% --port %APP_PORT% %RELOAD_FLAG%
)
