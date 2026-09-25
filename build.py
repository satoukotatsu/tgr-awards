#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/awards.json から index.html と awards-data.md を再生成する。

使い方: python build.py
標準ライブラリのみ使用。
"""
import html
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "data" / "awards.json"

GENERATED_NOTICE = "このファイルは build.py により data/awards.json から自動生成されています。直接編集しないでください。"


def esc(s):
    return html.escape(s, quote=True)


def source_html(src):
    """出典項目をHTML化。urlがlabel内に含まれる場合はその部分をリンク化する。"""
    label = src["label"]
    url = src.get("url")
    if url and url in label:
        link = '<a href="{0}">{0}</a>'.format(esc(url))
        return esc(label).replace(esc(url), link)
    if url:
        return '<a href="{0}">{1}</a>'.format(esc(url), esc(label))
    return esc(label)


def system_notes_html(notes):
    items = []
    for n in notes:
        s = "<li><strong>{}</strong>：{}".format(esc(n["head"]), esc(n["body"]))
        if n.get("children"):
            s += "\n      <ul>\n"
            for c in n["children"]:
                s += "        <li><strong>{}</strong>：{}</li>\n".format(
                    esc(c["head"]), esc(c["body"]))
            s += "      </ul>"
        s += "</li>"
        items.append(s)
    return "\n".join(items)


def row_html(r):
    tr = '<tr class="grand">' if r.get("grand") else "<tr>"
    work = r.get("work") or "—"
    return ("      {}"
            "<td>{}</td><td>{}</td><td>{}</td></tr>").format(
                tr, esc(r["award"]), esc(r["recipient"]), esc(work))


def build_html(data):
    meta = data["meta"]
    years = data["years"]

    nav = "\n".join(
        '    <a href="#y{0}">{0}</a>'.format(y["year"]) for y in years)

    sections = []
    for y in years:
        out = ['<section id="y{}">'.format(y["year"])]
        out.append("  <h2>{}年</h2>".format(y["year"]))
        if y.get("label"):
            out.append('  <p class="note">{}</p>'.format(esc(y["label"])))
        out.append('  <div class="table-wrap">')
        out.append("  <table>")
        out.append("    <thead><tr><th>賞</th><th>受賞者・団体</th><th>作品</th></tr></thead>")
        out.append("    <tbody>")
        out.extend(row_html(r) for r in y["rows"])
        out.append("    </tbody>")
        out.append("  </table>")
        out.append("  </div>")
        for note in y.get("notes", []):
            out.append('  <p class="note">{}</p>'.format(esc(note)))
        if y.get("sources"):
            out.append('  <div class="sources">出典：')
            out.append("    <ul>")
            for s in y["sources"]:
                out.append("      <li>{}</li>".format(source_html(s)))
            out.append("    </ul>")
            out.append("  </div>")
        out.append("</section>")
        sections.append("\n".join(out))

    return """<!DOCTYPE html>
<!-- {notice} -->
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{desc}">
<title>{title}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>

<header>
  <h1>{title}</h1>
  <p class="lead">{lead}</p>
  <p>{intro}</p>
</header>

<div class="layout">

<aside class="sidenav">
  <p class="sidenav-title">年別</p>
  <nav class="yearnav" aria-label="年別ナビゲーション">
{nav}
  </nav>
</aside>

<div class="content">

<section id="about">
  <h2>賞について</h2>
  <ul>
{system_notes}
  </ul>
</section>

{sections}

</div>
</div>

<footer>
  <p>{footer}</p>
  <p>最終更新: {updated} ／ 出典は各年の出典欄を参照</p>
</footer>

</body>
</html>
""".format(
        notice=GENERATED_NOTICE,
        desc=esc(meta["description"]),
        title=esc(meta["title"]),
        lead=esc(meta["lead"]),
        intro=esc(meta["intro"]),
        nav=nav,
        system_notes=system_notes_html(meta["system_notes"]),
        sections="\n\n".join(sections),
        footer=esc(meta["footer"]),
        updated=esc(meta["updated"]),
    )


def system_notes_md(notes):
    lines = []
    for n in notes:
        lines.append("- **{}**: {}".format(n["head"], n["body"]))
        for c in n.get("children", []):
            lines.append("  - **{}**: {}".format(c["head"], c["body"]))
    return "\n".join(lines)


def row_md(r):
    work = r.get("work", "")
    # 『…』で始まらない作品欄（俳優賞の所属団体名など）は括弧書きとして出力
    if work and not work.startswith("『"):
        work = "（{}）".format(work)
    line = "- {} {}： {}{}".format(r["acc"], r["award"], r["recipient"], work)
    # 根拠・出処の注記は調査記録（md）にのみ残す
    if r.get("ev"):
        line += "（{}）".format(r["ev"])
    return line


def build_md(data):
    meta = data["meta"]
    legend = meta["legend"]
    legend_md = "、".join("{}={}".format(k, v) for k, v in legend.items())

    parts = [
        "<!-- {} -->".format(GENERATED_NOTICE),
        "# {}データ（調査結果）".format(meta["title"]),
        meta["intro_md"],
        "## 賞の仕組み・名称変遷（年表に記す凡例）",
        system_notes_md(meta["system_notes"]),
        "凡例： " + legend_md,
        "---",
    ]

    for y in data["years"]:
        head = "## {}年".format(y["year"])
        if y.get("label"):
            head += "（{}）".format(y["label"])
        lines = [head, ""]
        lines.extend(row_md(r) for r in y["rows"])
        for note in y.get("notes", []) + y.get("research_notes", []):
            if note.startswith("公式注記"):
                lines.append("- " + note)
            else:
                lines.append("- 注記： " + note)
        if y.get("sources"):
            def src_md(s):
                return s["label"] + ("（{}）".format(s["url"]) if s.get("url") else "")
            lines.append("- 出典: " + ", ".join(src_md(s) for s in y["sources"]))
        parts.append("\n".join(lines))

    parts.append("---\n\n" + data["appendix_md"])
    return "\n\n".join(parts) + "\n"


def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    (BASE / "index.html").write_text(build_html(data), encoding="utf-8")
    (BASE / "awards-data.md").write_text(build_md(data), encoding="utf-8")
    print("generated: index.html, awards-data.md")


if __name__ == "__main__":
    main()
