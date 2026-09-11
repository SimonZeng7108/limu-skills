"""Export Xiaohongshu comment threads JSON into one txt file per conversation."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
COMMENTS = ROOT / "comments"
BEIJING = timezone(timedelta(hours=8))


def safe_name(text: str, limit: int = 40) -> str:
    text = re.sub(r'[\\/:*?"<>|\s]+', "_", text or "").strip("_")
    text = re.sub(r"_+", "_", text)
    return (text or "user")[:limit]


def format_time(ms) -> str:
    if not ms:
        return ""
    try:
        dt = datetime.fromtimestamp(int(ms) / 1000, tz=BEIJING)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ms)


def format_comment(prefix: str, item: dict) -> str:
    nick = item.get("nickname") or "未知用户"
    tags = item.get("tags") or []
    if isinstance(tags, dict):
        tags = list(tags.values())
    author = " [作者]" if "is_author" in tags else ""
    when = format_time(item.get("createTime"))
    loc = item.get("ipLocation") or ""
    meta = " · ".join(x for x in (when, loc) if x)
    reply_to = item.get("replyTo") or ""
    body = (item.get("content") or "").strip()
    lines = [f"{prefix}{nick}{author}"]
    if meta:
        lines.append(f"时间: {meta}")
    if reply_to:
        lines.append(f"回复: @{reply_to}")
    lines.append(body)
    return "\n".join(lines)


def thread_text(thread: dict, index: int) -> str:
    parts = [
        f"对话 {index:04d}",
        f"评论ID: {thread.get('id', '')}",
        "",
        format_comment("", thread),
    ]
    subs = thread.get("subComments") or []
    if subs:
        parts.append("")
        parts.append("--- 回复 ---")
        for sub in subs:
            parts.append("")
            parts.append(format_comment("", sub))
    parts.append("")
    return "\n".join(parts)


def main() -> None:
    src = DATA / "threads.json"
    if not src.exists():
        raise SystemExit(f"missing {src}")
    threads = json.loads(src.read_text(encoding="utf-8"))
    COMMENTS.mkdir(parents=True, exist_ok=True)
    written = 0
    for i, thread in enumerate(threads, start=1):
        nick = safe_name(thread.get("nickname") or "user")
        cid = (thread.get("id") or f"{i:04d}")[-8:]
        path = COMMENTS / f"{i:04d}_{nick}_{cid}.txt"
        path.write_text(thread_text(thread, i), encoding="utf-8")
        written += 1
    print(f"wrote {written} files to {COMMENTS}")


if __name__ == "__main__":
    main()
