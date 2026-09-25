# TGR札幌劇場祭 受賞歴

札幌劇場祭（TGR / Theater Go Round）2006–2025年の受賞結果を年別に一覧化した非公式まとめ。静的サイトとして公開・継続更新できる構成。

## 構成

```
data/awards.json   唯一のデータソース（全受賞行・注記・出典・確度）
build.py           生成スクリプト（標準ライブラリのみ）
style.css          index.html 用スタイル
index.html         生成物（直接編集しない）
awards-data.md     生成物（調査記録。直接編集しない）
```

## 更新手順

1. `data/awards.json` を編集する（`meta.updated` の日付も更新）
2. `python build.py` を実行 → `index.html` と `awards-data.md` が再生成される

JSON の各行は `{"award": 賞名, "recipient": 受賞者・団体, "work": 作品, "acc": "◎|○|△", "grand": true（大賞のみ）}`。年の補足は `label`、表の下の注記は `notes`、出典は `sources`（`url` が無い項目は `label` のみ）。

## 公開方法

`index.html`・`style.css`・`data/` をそのまま GitHub Pages 等の静的ホスティングに置く。JavaScript不使用のためビルド不要。
