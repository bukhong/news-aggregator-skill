"""
Convert enriched news JSON into a structured Markdown report.
Expects items to have AI-enriched fields: title_cn, summary, deep_dive.
Falls back gracefully if those fields are absent.

Usage:
    python3 scripts/auto_report.py <data.json> [--title "科技日报"] [--out report.md]
"""
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

SOURCE_EMOJI = {
    "Hacker News":     "🔥",
    "GitHub Trending": "🌟",
    "Product Hunt":    "🚀",
    "HF Papers":       "🤗",
    "36Kr":            "📰",
    "Wall Street CN":  "💹",
    "Weibo Hot Search":"🔴",
    "V2EX":            "💬",
    "Tencent News":    "📡",
    "BBC Chinese":     "🌐",
    "CNN":             "📺",
    "Reuters":         "📡",
    "SCMP":            "🗞️",
}

# Preferred display order
SOURCE_ORDER = [
    "BBC Chinese", "CNN", "Reuters", "SCMP",
    "Hacker News", "GitHub Trending", "Product Hunt",
    "HF Papers", "Wall Street CN", "36Kr",
    "Weibo Hot Search", "V2EX", "Tencent News",
]


def fmt_item(item: dict, idx: int) -> str:
    source    = item.get("source", "")
    raw_title = item.get("title", "").strip()
    title_cn  = item.get("title_cn", "").strip()
    url       = item.get("url", "")
    hn_url    = item.get("hn_url", "")
    heat      = item.get("heat", "")
    time_     = item.get("time", "Unknown Time")
    summary   = item.get("summary", "")
    deep_dive = item.get("deep_dive", "")
    lang      = item.get("lang", "")
    github    = item.get("github", "")

    # Use Chinese title if available, show original in parens
    if title_cn and title_cn != raw_title:
        display_title = f"{title_cn}（{raw_title}）"
    else:
        display_title = title_cn or raw_title

    link  = f"[{display_title}]({url})" if url else display_title
    lines = [f"#### {idx}. {link}"]

    # Meta
    meta = f"- **来源**: {source} | **时间**: {time_}"
    if heat:
        icon = "🌟" if "star" in heat.lower() else "🔥"
        meta += f" | **热度**: {icon} {heat}"
    if lang:
        meta += f" | **语言**: `{lang}`"
    lines.append(meta)

    # Extra links
    extras = []
    if hn_url:
        extras.append(f"[HN 讨论]({hn_url})")
    if github:
        extras.append(f"[GitHub]({github})")
    if extras:
        lines.append("- **链接**: " + " · ".join(extras))

    # Summary
    if summary:
        lines.append(f"- **摘要**: {summary}")

    # Deep Dive
    if deep_dive:
        lines.append(f"- **深度解读**: 💡 {deep_dive}")

    lines.append("")
    return "\n".join(lines)


def build_report(items: list, title: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    sections = defaultdict(list)
    for item in items:
        sections[item.get("source", "其他")].append(item)

    parts = [
        f"# {title}",
        f"> 生成时间：{now}  ·  共 {len(items)} 条",
        "",
    ]

    # Respect preferred order
    ordered = [s for s in SOURCE_ORDER if s in sections]
    ordered += [s for s in sections if s not in SOURCE_ORDER]

    for source in ordered:
        group = sections[source]
        emoji = SOURCE_EMOJI.get(source, "📌")
        parts.append(f"## {emoji} {source}\n")
        for i, item in enumerate(group, 1):
            parts.append(fmt_item(item, i))
        parts.append("---\n")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("data",    help="Path to JSON file (enriched or raw)")
    parser.add_argument("--title", default="",  help="Report title")
    parser.add_argument("--out",   default="",  help="Output markdown path")
    args = parser.parse_args()

    path  = Path(args.data)
    items = json.loads(path.read_text(encoding="utf-8"))
    title = args.title or f"每日资讯 · {datetime.now().strftime('%Y-%m-%d')}"

    report = build_report(items, title)

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"[Report] Saved → {out}")
    else:
        sys.stdout.buffer.write(report.encode("utf-8"))


if __name__ == "__main__":
    main()
