"""
Send a news report markdown file as an HTML email via SMTP.
Config via environment variables:
    EMAIL_FROM      sender address
    EMAIL_TO        recipient address (comma-separated for multiple)
    EMAIL_PASSWORD  SMTP password / app password
    SMTP_HOST       e.g. smtp.gmail.com  (default: smtp.gmail.com)
    SMTP_PORT       e.g. 587             (default: 587)

Usage:
    python3 scripts/send_email.py <report.md> [--subject "Daily Briefing"]
"""

import os
import sys
import argparse
import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime


def md_to_html(md: str) -> str:
    """Minimal Markdown → HTML conversion."""
    lines = md.splitlines()
    html_lines = []
    in_code = False

    for line in lines:
        # Code fences
        if line.strip().startswith("```"):
            if not in_code:
                html_lines.append("<pre><code>")
                in_code = True
            else:
                html_lines.append("</code></pre>")
                in_code = False
            continue
        if in_code:
            html_lines.append(line.replace("<", "&lt;").replace(">", "&gt;"))
            continue

        # Headings
        if line.startswith("#### "):
            html_lines.append(f"<h4>{_inline(line[5:])}</h4>")
        elif line.startswith("### "):
            html_lines.append(f"<h3>{_inline(line[4:])}</h3>")
        elif line.startswith("## "):
            html_lines.append(f"<h2 style='border-bottom:1px solid #eee;padding-bottom:4px'>{_inline(line[3:])}</h2>")
        elif line.startswith("# "):
            html_lines.append(f"<h1 style='color:#1a73e8'>{_inline(line[2:])}</h1>")
        # Horizontal rule
        elif re.match(r"^-{3,}$", line):
            html_lines.append("<hr style='border:none;border-top:1px solid #eee'>")
        # Blockquote
        elif line.startswith("> "):
            html_lines.append(f"<blockquote style='color:#666;border-left:3px solid #ccc;margin:0;padding-left:12px'>{_inline(line[2:])}</blockquote>")
        # List item
        elif re.match(r"^[-*]\s", line):
            html_lines.append(f"<li>{_inline(line[2:])}</li>")
        # Empty line
        elif line.strip() == "":
            html_lines.append("<br>")
        else:
            html_lines.append(f"<p style='margin:4px 0'>{_inline(line)}</p>")

    return "\n".join(html_lines)


def _inline(text: str) -> str:
    """Handle inline markdown: bold, links."""
    # Links [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                  r'<a href="\2" style="color:#1a73e8">\1</a>', text)
    # Bold **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return text


def build_html(content: str, title: str) -> str:
    body = md_to_html(content)
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, "PingFang SC", sans-serif; font-size: 14px;
          color: #333; max-width: 800px; margin: auto; padding: 24px; }}
  h2 {{ margin-top: 24px; }}
  h4 {{ margin: 12px 0 4px; }}
  li {{ margin: 2px 0; }}
  pre {{ background:#f6f8fa; padding:12px; border-radius:4px; overflow:auto; }}
  hr {{ margin: 16px 0; }}
  blockquote {{ font-size:12px; }}
</style>
</head>
<body>
{body}
<br><hr>
<small style="color:#999">自动推送 · News Agent · {datetime.now().strftime('%Y-%m-%d %H:%M')}</small>
</body>
</html>"""


def send(report_path: Path, subject: str) -> bool:
    from_addr  = os.environ.get("EMAIL_FROM", "")
    to_addrs   = [a.strip() for a in os.environ.get("EMAIL_TO", "").split(",") if a.strip()]
    password   = os.environ.get("EMAIL_PASSWORD", "")
    smtp_host  = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port  = int(os.environ.get("SMTP_PORT", "587"))

    if not all([from_addr, to_addrs, password]):
        print("[Email] SKIP — EMAIL_FROM / EMAIL_TO / EMAIL_PASSWORD not set")
        return True  # non-fatal

    content = report_path.read_text(encoding="utf-8")
    html    = build_html(content, subject)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = from_addr
    msg["To"]      = ", ".join(to_addrs)
    msg.attach(MIMEText(content, "plain", "utf-8"))
    msg.attach(MIMEText(html,    "html",  "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(from_addr, password)
            server.sendmail(from_addr, to_addrs, msg.as_string())
        print(f"[Email] OK sent to {', '.join(to_addrs)}")
        return True
    except Exception as e:
        print(f"[Email] FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", help="Path to report markdown file")
    parser.add_argument("--subject", default="", help="Email subject")
    args = parser.parse_args()

    path = Path(args.report)
    if not path.exists():
        print(f"[Email] File not found: {path}")
        sys.exit(1)

    subject = args.subject or f"每日简报 {datetime.now().strftime('%Y-%m-%d')} — {path.stem}"
    ok = send(path, subject)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
