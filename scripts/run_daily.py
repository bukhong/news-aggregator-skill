"""
Daily automation orchestrator.
  1. Fetch news       (fetch_news.py)
  2. AI enrichment    (enrich_with_ai.py) — translate + summary + deep dive
  3. Format report    (auto_report.py)
  4. Send email       (send_email.py)
  5. Push to Feishu   (send_to_feishu.py)

Usage:
    python3 scripts/run_daily.py [--profile tech|ai|finance|social|general|world]

Environment variables:
    ANTHROPIC_API_KEY  For AI enrichment (translation + summaries)
    FEISHU_WEBHOOK     Feishu bot webhook URL
    EMAIL_FROM         sender email
    EMAIL_TO           recipient email(s), comma-separated
    EMAIL_PASSWORD     SMTP password / app-password
    SMTP_HOST          default: smtp.gmail.com
    SMTP_PORT          default: 587
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports" / datetime.now().strftime("%Y-%m-%d")

PROFILE_SOURCES = {
    "tech":    "hackernews,github,producthunt",
    "ai":      "huggingface,ai_newsletters",
    "finance": "wallstreetcn,36kr,tencent",
    "social":  "weibo,v2ex,tencent",
    "world":   "bbc,cnn,reuters,scmp",
    "general": "hackernews,github,producthunt,36kr,wallstreetcn,weibo,bbc,reuters",
}

PROFILE_TITLES = {
    "tech":    "科技日报",
    "ai":      "AI 日报",
    "finance": "财经日报",
    "social":  "社交热点",
    "world":   "国际要闻",
    "general": "综合日报",
}


def run(cmd: list, env: dict = None) -> int:
    print(f"[Run] {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(
        cmd,
        env=env or {**os.environ, "PYTHONIOENCODING": "utf-8"}
    )
    return result.returncode


def step_fetch(sources: str, limit: int = 15) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

    subprocess.run(
        [sys.executable, ROOT / "scripts" / "fetch_news.py",
         "--source", sources, "--limit", str(limit),
         "--save", "--outdir", str(REPORTS_DIR)],
        env=env, capture_output=True
    )

    jsons = sorted(REPORTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not jsons:
        print("[Fetch] ERROR: no JSON output found")
        sys.exit(1)
    latest = jsons[-1]
    print(f"[Fetch] OK → {latest}")
    return latest


def step_enrich(json_path: Path) -> Path:
    """AI translate + summarize. Returns same path (enriched in-place)."""
    if not os.environ.get("OPENAI_API_KEY"):
        print("[Enrich] SKIP — OPENAI_API_KEY not set")
        return json_path

    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    rc = run(
        [sys.executable, ROOT / "scripts" / "enrich_with_ai.py", str(json_path)],
        env=env
    )
    if rc == 0:
        print(f"[Enrich] OK → {json_path}")
    else:
        print("[Enrich] WARNING: enrichment failed, continuing with raw data")
    return json_path


def step_format(json_path: Path, title: str) -> Path:
    ts     = datetime.now().strftime("%H%M")
    md_out = REPORTS_DIR / f"daily_report_{ts}.md"
    env    = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    run(
        [sys.executable, ROOT / "scripts" / "auto_report.py",
         str(json_path), "--title", title, "--out", str(md_out)],
        env=env
    )
    print(f"[Format] OK → {md_out}")
    return md_out


def step_email(md_path: Path, title: str):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    run(
        [sys.executable, ROOT / "scripts" / "send_email.py",
         str(md_path), "--subject", f"{title} · {datetime.now().strftime('%Y-%m-%d')}"],
        env=env
    )


def step_feishu(md_path: Path):
    webhook = os.environ.get(
        "FEISHU_WEBHOOK",
        "https://open.feishu.cn/open-apis/bot/v2/hook/87d5d92a-8e25-4a3b-ad8e-a42b58f4a8fa"
    )
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    run(
        [sys.executable, ROOT / "scripts" / "send_to_feishu.py",
         str(md_path), "--webhook", webhook],
        env=env
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="general",
                        choices=list(PROFILE_SOURCES.keys()))
    parser.add_argument("--limit",      type=int, default=10)
    parser.add_argument("--no-enrich",  action="store_true", help="Skip AI enrichment")
    parser.add_argument("--no-email",   action="store_true")
    parser.add_argument("--no-feishu",  action="store_true")
    args = parser.parse_args()

    sources = PROFILE_SOURCES[args.profile]
    title   = PROFILE_TITLES[args.profile]

    print(f"\n=== {title} · {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")

    json_path = step_fetch(sources, args.limit)

    if not args.no_enrich:
        json_path = step_enrich(json_path)

    md_path = step_format(json_path, title)

    if not args.no_email:
        step_email(md_path, title)

    if not args.no_feishu:
        step_feishu(md_path)

    print(f"\n=== Done → {md_path} ===\n")


if __name__ == "__main__":
    main()
