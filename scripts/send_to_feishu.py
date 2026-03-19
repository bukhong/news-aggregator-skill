"""
Send a news report markdown file to Feishu via webhook (card message).
Usage:
    python3 scripts/send_to_feishu.py <report.md>
    python3 scripts/send_to_feishu.py <report.md> --webhook <url>
"""

import sys
import json
import re
import argparse
import requests
from pathlib import Path
from datetime import datetime

# Default webhook — override with --webhook or FEISHU_WEBHOOK env var
DEFAULT_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/87d5d92a-8e25-4a3b-ad8e-a42b58f4a8fa"

# Feishu card content limit per element (chars)
CHUNK_SIZE = 4000

# Header colour by briefing type
HEADER_COLOURS = {
    "tech":    "blue",
    "ai":      "purple",
    "finance": "green",
    "social":  "orange",
    "general": "turquoise",
}


def md_to_lark(text: str) -> str:
    """Convert a subset of Markdown to Feishu lark_md."""
    # #### headings → **bold**
    text = re.sub(r"^#{1,4}\s+(.+)$", r"**\1**", text, flags=re.MULTILINE)
    # --- dividers → blank line (feishu has its own divider element)
    text = re.sub(r"^-{3,}$", "", text, flags=re.MULTILINE)
    # Tables → keep as-is (lark_md supports simple tables)
    # Bullet lists: keep */-/• as-is
    # Strip HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Collapse 3+ blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks without breaking lines."""
    chunks, current = [], []
    length = 0
    for line in text.splitlines(keepends=True):
        if length + len(line) > size and current:
            chunks.append("".join(current))
            current, length = [], 0
        current.append(line)
        length += len(line)
    if current:
        chunks.append("".join(current))
    return chunks


def build_card(title: str, body: str, source_file: str) -> dict:
    """Build a Feishu interactive card from title + markdown body."""
    # Pick header colour
    colour = "blue"
    for key, col in HEADER_COLOURS.items():
        if key in title.lower() or key in source_file.lower():
            colour = col
            break

    lark_body = md_to_lark(body)
    chunks = chunk_text(lark_body)

    elements = []
    for i, chunk in enumerate(chunks):
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": chunk}
        })
        if i < len(chunks) - 1:
            elements.append({"tag": "hr"})

    # Footer
    elements.append({"tag": "hr"})
    elements.append({
        "tag": "note",
        "elements": [{
            "tag": "plain_text",
            "content": f"📁 {source_file}  ·  🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        }]
    })

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": colour
            },
            "elements": elements
        }
    }


def send(webhook: str, card: dict) -> bool:
    """POST card to Feishu webhook. Returns True on success."""
    try:
        resp = requests.post(
            webhook,
            json=card,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        result = resp.json()
        if result.get("code") == 0 or result.get("StatusCode") == 0:
            print("[Feishu] OK Sent successfully")
            return True
        else:
            print(f"[Feishu] ERROR: {result}")
            return False
    except Exception as e:
        print(f"[Feishu] FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Send news report to Feishu")
    parser.add_argument("report", help="Path to report markdown file")
    parser.add_argument("--webhook", default=DEFAULT_WEBHOOK, help="Feishu webhook URL")
    parser.add_argument("--title", default="", help="Override card title")
    args = parser.parse_args()

    path = Path(args.report)
    if not path.exists():
        print(f"[Feishu] File not found: {path}")
        sys.exit(1)

    content = path.read_text(encoding="utf-8")

    # Auto-detect title from first H1 or filename
    title = args.title
    if not title:
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = match.group(1) if match else path.stem.replace("_", " ").title()

    card = build_card(title, content, path.name)
    success = send(args.webhook, card)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
