# astrology

`astrology.py` を正本として、Swiss Ephemeris の参照先を **環境変数 + 自動探索** で統一しました。
Notebook / FastAPI / スクリプトのどこから呼んでも同じ解決ロジックを使います。

## Ephemeris の配置場所（推奨）

以下のいずれかに配置してください（未指定時の探索候補）:

- `ephe/`
- `ephemeris/`
- `data/ephe/`
- `data/ephemeris/`
- `cwd/ephe/`
- `cwd/ephemeris/`
- さらに `ephe` を含むディレクトリ名を repo 直下 / 実行カレント直下から動的探索

> このリポジトリでは `sepl_18.se1` などが repo 直下にある場合も検出されます。

## 環境変数で明示指定

```bash
ASTROLOGY_EPHE_PATH=/path/to/ephemeris
```

- 指定時は最優先で使用
- 空欄なら自動探索

`.env.example` では次のように設定しています:

```env
ASTROLOGY_EPHE_PATH=
RESULT_OUTPUT_DIR=data/results
APP_ENV=dev
```

## 自動探索の仕様

`astrology.configure_ephemeris()` は次を実施します。

1. `ASTROLOGY_EPHE_PATH` を確認
2. repo / cwd の候補ディレクトリを順次探索
3. Swiss Ephemeris らしいファイル（`se*.se1` 複数、または `sefstars.txt`）を検証
4. 見つかったパスを `swe.set_ephe_path(...)` に設定
5. 解決元と採用パスをログ表示

見つからない場合は、探索した候補一覧付きでエラーを返します。

## Colab での使い方

```python
!git clone <repo-url>
%cd astrology
!pip install -r requirements.txt

import astrology
astrology.print_ephemeris_status()
```

`ASTROLOGY_EPHE_PATH` を固定で書かなくても、repo 内の候補から自動検出します。

## Windows / Linux での使い方

### Windows (PowerShell)

```powershell
git clone <repo-url>
cd astrology
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
$env:ASTROLOGY_EPHE_PATH = "C:\path\to\ephemeris"  # 任意
python scripts/run_natal_example.py
```

### Linux / macOS

```bash
git clone <repo-url>
cd astrology
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ASTROLOGY_EPHE_PATH=/path/to/ephemeris  # 任意
python scripts/run_natal_example.py
```

## FastAPI との整合

FastAPI (`app/services/astrology_service.py`) でも `astrology.configure_ephemeris(...)` を呼ぶため、
Web/API 実行時も同じ解決ロジックになります。

## 動作確認

```bash
python -c "import astrology; astrology.print_ephemeris_status()"
python scripts/run_natal_example.py
```

最低ライン:

- `import astrology` が成功
- ephemeris path が解決される
- natal レポートが生成される
