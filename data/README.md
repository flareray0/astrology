# data directory

このディレクトリはローカル実行時の入力データ/出力データ置き場です。

## 推奨構成

```
data/
  ephe/      # Swiss Ephemeris の .se1/.se2/.sef ファイルを配置
  results/   # API や script 実行で生成される結果ファイル
```

- `ephe/` は Git 管理対象外（`.gitignore`）です。
- `results/` も生成物を Git から除外しています。
