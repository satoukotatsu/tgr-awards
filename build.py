#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/awards.json から index.html と awards-data.md を再生成する。

使い方: python build.py
標準ライブラリのみ使用。
"""
import html
import json
from collections import Counter
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


# 色は CSS の currentColor / class に任せ、SVG 側にリテラルを持たせない
ICONS = {
    "trophy": '<path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4z"/><path d="M7 6H4v1a3 3 0 0 0 3 3M17 6h3v1a3 3 0 0 1-3 3"/>',
    "medal": '<circle cx="12" cy="15" r="5"/><path d="M8.5 10.5 6 3h4l2 4 2-4h4l-2.5 7.5"/>',
    "eye": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "sprout": '<path d="M12 21v-9"/><path d="M12 12c0-4-3-6-7-6 0 4 3 6 7 6z"/><path d="M12 14c0-3 2.5-5 6-5 0 3-2.5 5-6 5z"/>',
    "mask": '<path d="M4 5h16v6a8 8 0 0 1-16 0V5z"/><path d="M8 10h2M14 10h2M9 15c1.5 1.5 4.5 1.5 6 0"/>',
    "users": '<circle cx="9" cy="8" r="3"/><path d="M3 20v-1a5 5 0 0 1 5-5h2a5 5 0 0 1 5 5v1"/><path d="M16 5.2a3 3 0 0 1 0 5.6M21 20v-1a5 5 0 0 0-3.5-4.8"/>',
    "scale": '<path d="M12 3v18M7 21h10M5 7h14"/><path d="M5 7l-3 7a3 3 0 0 0 6 0L5 7zM19 7l-3 7a3 3 0 0 0 6 0l-3-7z"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "crown": '<path d="M3 8l4.5 4L12 5l4.5 7L21 8l-2 11H5L3 8z"/>',
}


def icon_svg(name, size, cls="icon"):
    return ('<svg class="{}" width="{}" height="{}" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true">{}</svg>').format(
                cls, size, size, ICONS[name])


def stage_illustration():
    """ヒーロー用の舞台イラスト。配色は style.css の .stage-* 側で当てる。"""
    banner = "M300 14V28" + "q-14 14-28 0" * 10 + "V14z"
    return """<svg class="stage" viewBox="0 0 320 240" role="img" aria-label="劇場の舞台とトロフィーのイラスト" stroke-linecap="round" stroke-linejoin="round">
      <path class="stage-spot" d="M148 34h24l56 156H92z"/>
      <path class="stage-banner" d="{banner}"/>
      <path class="stage-curtain" d="M20 30h50c-8 62 6 120-10 184H20z"/>
      <path class="stage-curtain" d="M300 30h-50c8 62-6 120 10 184h40z"/>
      <path class="stage-fold" d="M40 32c-4 60 4 120-2 180M54 32c-4 60 4 120 0 180"/>
      <path class="stage-fold" d="M280 32c4 60-4 120 2 180M266 32c4 60-4 120 0 180"/>
      <ellipse class="stage-floor" cx="160" cy="200" rx="96" ry="18"/>
      <g class="stage-trophy">
        <path class="stage-cup" d="M138 108h44v28a22 22 0 0 1-44 0z"/>
        <path d="M138 114h-12v6a12 12 0 0 0 12 12M182 114h12v6a12 12 0 0 1-12 12"/>
        <path d="M160 158v18M148 176h24v14h-24zM140 190h40"/>
      </g>
    </svg>""".format(banner=banner)


def stats_html(years):
    rows = [r for y in years for r in y["rows"]]
    awards = sum(1 for r in rows if r["recipient"] != "該当なし")
    grand = Counter(r["recipient"] for r in rows if r.get("grand"))
    top = max(grand.values())
    # 同数なら年が古い方: Counter は挿入順を保つので先頭の最大値を採る
    name = next(k for k, v in grand.items() if v == top)
    items = [
        ("calendar", str(len(years)), "年分の記録"),
        ("trophy", str(awards), "の受賞"),
        ("crown", str(top), "{}（大賞最多）".format(esc(name))),
    ]
    out = ['<ul class="stats">']
    for icon, num, label in items:
        out.append('  <li>{}<div><p class="stat-num">{}</p><p class="stat-label">{}</p></div></li>'.format(
            icon_svg(icon, 24), num, label))
    out.append("</ul>")
    return "\n".join(out), (len(years), awards, top, name)


def system_notes_html(notes):
    cards = []
    for n in notes:
        s = ('  <article class="about-card">\n'
             '    <span class="about-icon">{}</span>\n'
             '    <h3>{}</h3>\n'
             '    <p>{}</p>').format(icon_svg(n["icon"], 22), esc(n["head"]), esc(n["body"]))
        if n.get("children"):
            s += "\n    <ul>\n"
            for c in n["children"]:
                s += "      <li><strong>{}</strong>：{}</li>\n".format(
                    esc(c["head"]), esc(c["body"]))
            s += "    </ul>"
        s += "\n  </article>"
        cards.append(s)
    return "\n".join(cards)


def award_list_html(rows, indent):
    pad = " " * indent
    items = []
    for r in rows:
        if r.get("grand"):
            continue
        dd = esc(r["recipient"])
        if r.get("work"):
            dd += ' <span class="work">{}</span>'.format(esc(r["work"]))
        items.append("{0}  <dt>{1}</dt><dd>{2}</dd>".format(pad, esc(r["award"]), dd))
    if not items:
        return []
    return [pad + '<dl class="award-list">'] + items + [pad + "</dl>"]


def tail_html(y, indent):
    pad = " " * indent
    out = []
    for note in y.get("notes", []):
        out.append('{}<p class="note">{}</p>'.format(pad, esc(note)))
    if y.get("sources"):
        out.append('{}<div class="sources">出典：'.format(pad))
        out.append("{}  <ul>".format(pad))
        for s in y["sources"]:
            out.append("{}    <li>{}</li>".format(pad, source_html(s)))
        out.append("{}  </ul>".format(pad))
        out.append("{}</div>".format(pad))
    return out


def grand_row(y):
    return next(r for r in y["rows"] if r.get("grand"))


def latest_html(y):
    g = grand_row(y)
    out = ['<section id="y{}" class="latest">'.format(y["year"])]
    out.append('  <div class="year-head"><span class="badge">最新</span><h2>{}年</h2></div>'.format(y["year"]))
    if y.get("label"):
        out.append('  <p class="note">{}</p>'.format(esc(y["label"])))
    out.append('  <div class="grand-feature">')
    out.append('    <p class="grand-award">{}</p>'.format(esc(g["award"])))
    out.append('    <p class="grand-recipient">{}</p>'.format(esc(g["recipient"])))
    if g.get("work"):
        out.append('    <p class="grand-work">{}</p>'.format(esc(g["work"])))
    out.append("    " + icon_svg("trophy", 48, "icon grand-icon"))
    out.append("  </div>")
    out.extend(award_list_html(y["rows"], 2))
    out.extend(tail_html(y, 2))
    out.append("</section>")
    return "\n".join(out)


def past_year_html(y):
    g = grand_row(y)
    out = ['  <details id="y{}" class="year">'.format(y["year"])]
    out.append("    <summary>")
    out.append('      <span class="y">{}</span>'.format(y["year"]))
    out.append('      <span class="who">{}</span>'.format(esc(g["recipient"])))
    out.append('      <span class="work">{}</span>'.format(esc(g.get("work") or "")))
    out.append("    </summary>")
    out.append('    <div class="year-body">')
    if y.get("label"):
        out.append('      <p class="note">{}</p>'.format(esc(y["label"])))
    out.extend(award_list_html(y["rows"], 6))
    out.extend(tail_html(y, 6))
    out.append("    </div>")
    out.append("  </details>")
    return "\n".join(out)


def build_html(data):
    meta = data["meta"]
    years = data["years"]
    latest = years[-1]
    past = list(reversed(years[:-1]))

    stats_block, _ = stats_html(years)
    latest_section = latest_html(latest)
    past_section = "\n".join(
        ['<section id="past" class="past">', "  <h2>過去の受賞</h2>",
         '  <div class="past-head" aria-hidden="true"><span>年</span><span>大賞</span><span>作品</span></div>']
        + [past_year_html(y) for y in past]
        + ["</section>"])

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
  <div class="hero-text">
    <p class="eyebrow">{y0}–{y1}</p>
    <h1>{title}</h1>
    <p class="intro">{intro}</p>
    <p class="lead">{lead}</p>
  </div>
  <div class="hero-art">
    {stage}
  </div>
</header>

<div class="layout">

{stats}

{latest}

{past}

<section id="about">
  <h2>賞のしくみ</h2>
  <div class="about-grid">
{system_notes}
  </div>
</section>

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
        y0=years[0]["year"],
        y1=years[-1]["year"],
        stage=stage_illustration(),
        stats=stats_block,
        latest=latest_section,
        past=past_section,
        system_notes=system_notes_html(meta["system_notes"]),
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
