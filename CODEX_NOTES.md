# Codex向け補助メモ

## 目的
この土台に対して、既存の astrology.py をつなぎ込み、
localhost で動くプロ品質の占星アプリへ仕上げる。

## 最重要タスク
1. `web/app.py` から `astrology.py` を呼び出す
2. `build_chart_from_input(...)` と `run_report_by_mode(...)` を使って全モード接続
3. ephemeris 自動検出
4. notebook と .py のロジック差分を減らす
5. natal / progressed / transit / triple / synastry の文章品質を上げる

## チェックリスト
- [ ] `uvicorn web.app:app --reload` で起動
- [ ] `/health` が ok
- [ ] フォームから natal 実行
- [ ] synastry 実行
- [ ] repo 内 ephemeris から正常計算

---
# Codex Support Notes (English)

## Objective
Integrate the existing `astrology.py` into a professional local astrology app that runs on localhost.

## Highest-priority tasks
1. Call `astrology.py` from `web/app.py`.
2. Connect all chart modes using `build_chart_from_input(...)` and `run_report_by_mode(...)`.
3. Enable ephemeris auto-detection.
4. Reduce logic drift between notebook and `.py` implementation.
5. Improve report quality for natal / progressed / transit / triple / synastry.

## Checklist
- [ ] `uvicorn web.app:app --reload` starts successfully.
- [ ] `/health` returns ok.
- [ ] Natal can be generated from form input.
- [ ] Synastry can be generated from form input.
- [ ] Ephemeris inside the repository is detected and used.

