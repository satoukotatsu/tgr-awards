#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/awards.json から index.html（表紙）・年別ページ YYYY.html・awards-data.md を再生成する。

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


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;500'
         '&family=Shippori+Mincho:wght@400;500;700&display=swap" rel="stylesheet">')


def edition(y):
    """第N回。2006年が第1回で、ページ番号（ノンブル）にも使う。"""
    return y["year"] - 2005


def page_file(y):
    return "{}.html".format(y["year"])


def spine_html(years, current=None):
    """current が None のときは表紙（目次）を現在ページとして扱う。"""
    toc_cur = ' aria-current="page"' if current is None else ""
    out = ['<nav class="spine" aria-label="年">',
           # 縦の背表紙では「目次」、スマホの上部バーではサイト名として表紙へ戻るリンクになる
           '  <a class="spine-toc" href="index.html"{}><span class="spine-site">TGR受賞歴</span>'
           '<span class="spine-toc-label">目次</span></a>'.format(toc_cur)]
    for y in reversed(years):
        cur = ' aria-current="page"' if y is current else ""
        out.append('  <a href="{}"{}>{}</a>'.format(page_file(y), cur, y["year"]))
    out.append("</nav>")
    return "\n".join(out)


def winner_html(i, r):
    cls = []
    if r.get("grand"):
        cls.append("grand")
    if r["recipient"] == "該当なし":
        cls.append("none")
    attr = ' class="{}"'.format(" ".join(cls)) if cls else ""
    body = '<p class="name">{}</p>'.format(esc(r["recipient"]))
    if r.get("work"):
        body += '<p class="work">{}</p>'.format(esc(r["work"]))
    return ('    <li{} style="--i: {}">\n'
            '      <span class="award">{}</span>\n'
            '      <div>{}</div>\n'
            '    </li>').format(attr, i, esc(r["award"]), body)


def sources_html(y):
    if not y.get("sources"):
        return ""
    out = ['  <section class="sources">', "    <h2>出典</h2>", "    <ol>"]
    out += ["      <li>{}</li>".format(source_html(s)) for s in y["sources"]]
    out += ["    </ol>", "  </section>"]
    return "\n".join(out)


def turn_html(prev, nxt):
    left = '<a href="{}" rel="prev">← {}</a>'.format(page_file(prev), prev["year"]) if prev else "<span></span>"
    right = '<a href="{}" rel="next">{} →</a>'.format(page_file(nxt), nxt["year"]) if nxt else "<span></span>"
    return '  <nav class="turn" aria-label="前後の年">\n    {}\n    {}\n  </nav>'.format(left, right)


def page_shell(title, desc, spine, main):
    return """<!DOCTYPE html>
<!-- {notice} -->
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{desc}">
<title>{title}</title>
{fonts}
<link rel="stylesheet" href="style.css">
</head>
<body>
{spine}

{main}
</body>
</html>
""".format(notice=GENERATED_NOTICE, desc=esc(desc), title=esc(title),
           fonts=FONTS, spine=spine, main=main)


def year_page_html(data, idx):
    meta = data["meta"]
    years = data["years"]
    y = years[idx]
    prev = years[idx - 1] if idx > 0 else None
    nxt = years[idx + 1] if idx + 1 < len(years) else None
    g = next(r for r in y["rows"] if r.get("grand"))

    out = ['<main class="page">',
           '  <section class="year">',
           '    <p class="eyebrow">第{}回</p>'.format(edition(y)),
           "    <h1>{}</h1>".format(y["year"]),
           '    <span class="year-unit">年</span>']
    if y.get("label"):
        out.append('    <p class="year-label">{}</p>'.format(esc(y["label"])))
    out += ["  </section>", "", '  <ol class="winners">']
    out += [winner_html(i, r) for i, r in enumerate(y["rows"], 1)]
    out.append("  </ol>")
    for note in y.get("notes", []):
        out.append('  <p class="notes">{}</p>'.format(esc(note)))
    out += ["", sources_html(y), "", turn_html(prev, nxt), "",
            '  <p class="disclaimer">{}</p>'.format(esc(meta["lead"])),
            '  <footer class="folio">— {} —</footer>'.format(edition(y)),
            "</main>"]

    title = "{}年 | {}".format(y["year"], meta["title"])
    desc = "{} {}年（第{}回）の受賞結果。大賞：{}{}。非公式のまとめ。".format(
        meta["title"], y["year"], edition(y), g["recipient"], g.get("work", ""))
    return page_shell(title, desc, spine_html(years, y), "\n".join(out))


def system_notes_html(notes):
    out = ['    <dl>']
    for n in notes:
        out.append("      <dt>{}</dt>".format(esc(n["head"])))
        dd = esc(n["body"])
        if n.get("children"):
            dd += "<ul>" + "".join("<li><strong>{}</strong>：{}</li>".format(
                esc(c["head"]), esc(c["body"])) for c in n["children"]) + "</ul>"
        out.append("      <dd>{}</dd>".format(dd))
    out.append("    </dl>")
    return "\n".join(out)


def cover_html(data):
    """表紙：題名・はしがき・目次・賞のしくみ・奥付。"""
    meta = data["meta"]
    years = data["years"]
    y0, y1 = years[0]["year"], years[-1]["year"]

    toc = []
    for y in reversed(years):
        g = next(r for r in y["rows"] if r.get("grand"))
        grand = '<span class="toc-name">{}</span>'.format(esc(g["recipient"]))
        if g.get("work"):
            grand += '<span class="toc-work">{}</span>'.format(esc(g["work"]))
        toc.append('      <li><a href="{}"><span class="toc-year">{}</span>'
                   '<span class="toc-grand">{}</span><span class="toc-folio">{}</span></a></li>'.format(
                       page_file(y), y["year"], grand, edition(y)))

    main = """<main class="page cover">
  <section class="cover-title">
    <p class="eyebrow">札幌劇場祭 TGR　第1回–第{e1}回</p>
    <p class="cover-years">{y0}<span>–</span>{y1}</p>
    <h1>{title_phrases}</h1>
    <p class="intro">{intro}</p>
  </section>

  <section class="toc">
    <h2>目次</h2>
    <p class="toc-head" aria-hidden="true"><span>年</span><span>大賞</span><span>頁</span></p>
    <ol>
{toc}
    </ol>
  </section>

  <section class="system">
    <h2>賞のしくみ</h2>
{system}
  </section>

  <footer class="colophon">
    <p>{lead}</p>
    <p>{footer}</p>
    <p>最終更新 {updated}</p>
  </footer>
</main>""".format(
        e1=edition(years[-1]), y0=y0, y1=y1,
        # 狭い画面で「受／賞歴」のように語の途中で折り返さないよう、空白区切りの語ごとに包む
        title_phrases=" ".join('<span class="phrase">{}</span>'.format(esc(w)) for w in meta["title"].split()),
        intro=esc(meta["intro"]), toc="\n".join(toc),
        system=system_notes_html(meta["system_notes"]),
        lead=esc(meta["lead"]), footer=esc(meta["footer"]), updated=esc(meta["updated"]))
    return page_shell(meta["title"], meta["description"], spine_html(years), main)


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
    (BASE / "index.html").write_text(cover_html(data), encoding="utf-8")
    for i, y in enumerate(data["years"]):
        (BASE / page_file(y)).write_text(year_page_html(data, i), encoding="utf-8")
    (BASE / "awards-data.md").write_text(build_md(data), encoding="utf-8")
    print("generated: index.html, {}-{}.html, awards-data.md".format(
        data["years"][0]["year"], data["years"][-1]["year"]))


if __name__ == "__main__":
    main()
