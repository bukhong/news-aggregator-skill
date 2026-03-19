"""
Enrich raw news JSON with AI-generated Chinese content using the Anthropic API.

For each item adds:
  title_cn   — Chinese translation of the title
  summary    — One-sentence Chinese summary
  deep_dive  — 2-3 sentence Chinese insight / analysis

Usage:
    python3 scripts/enrich_with_ai.py raw.json --out enriched.json
    python3 scripts/enrich_with_ai.py raw.json   # overwrites in-place

Requires:
    ANTHROPIC_API_KEY environment variable
    pip install anthropic
"""

import json
import os
import sys
import argparse
from pathlib import Path

BATCH_SIZE = 8   # items per API call


def enrich(items: list) -> list:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("[AI Enrich] SKIP — ANTHROPIC_API_KEY not set", file=sys.stderr)
        return items

    try:
        import anthropic
    except ImportError:
        print("[AI Enrich] SKIP — anthropic package not installed (pip install anthropic)", file=sys.stderr)
        return items

    client = anthropic.Anthropic(api_key=api_key)
    enriched = []

    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i:i + BATCH_SIZE]
        batch_input = [
            {"index": j, "title": item.get("title", ""), "content": item.get("content", "")[:1000]}
            for j, item in enumerate(batch)
        ]

        prompt = f"""你是一名专业的科技/财经新闻编辑。以下是一批英文新闻条目（JSON格式）。

请对每条新闻：
1. 将标题翻译成简体中文（title_cn）
2. 用一句话中文概括核心内容（summary，不超过60字）
3. 写2-3句深度分析（deep_dive），包含背景、影响或技术价值（不超过120字）

如果原标题已经是中文，title_cn 保持原文不变。
保留英文专有名词（如 OpenAI, GitHub, Python 等）。

输入：
{json.dumps(batch_input, ensure_ascii=False, indent=2)}

请严格按以下JSON格式输出，不要添加其他内容：
[
  {{"index": 0, "title_cn": "...", "summary": "...", "deep_dive": "..."}},
  ...
]"""

        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            text = resp.content[0].text.strip()

            # Parse JSON — strip markdown fences if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            results = json.loads(text)

            # Merge back
            for r in results:
                idx = r.get("index", 0)
                if 0 <= idx < len(batch):
                    batch[idx]["title_cn"]  = r.get("title_cn", batch[idx].get("title", ""))
                    batch[idx]["summary"]   = r.get("summary", "")
                    batch[idx]["deep_dive"] = r.get("deep_dive", "")

            print(f"[AI Enrich] Batch {i // BATCH_SIZE + 1}: {len(batch)} items enriched", file=sys.stderr)

        except Exception as e:
            print(f"[AI Enrich] Batch {i // BATCH_SIZE + 1} failed: {e}", file=sys.stderr)

        enriched.extend(batch)

    return enriched


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("data", help="Input JSON file (raw news items)")
    parser.add_argument("--out", default="", help="Output path (default: overwrite input)")
    args = parser.parse_args()

    path = Path(args.data)
    items = json.loads(path.read_text(encoding="utf-8"))

    enriched = enrich(items)

    out_path = Path(args.out) if args.out else path
    out_path.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[AI Enrich] Saved {len(enriched)} items → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
