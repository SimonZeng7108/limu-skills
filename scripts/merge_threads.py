"""Merge a threads JSON dump into data/threads.json and refresh txt files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
THREADS = DATA / "threads.json"


def load_json(path: Path):
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "result" in raw:
        val = raw["result"].get("value")
        if isinstance(val, str):
            return json.loads(val)
        if isinstance(val, list):
            return val
        if isinstance(val, dict) and "threads" in val:
            return val["threads"]
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and "threads" in raw:
        return raw["threads"]
    return []


def merge(old: list, new: list) -> list:
    by_id = {t.get("id"): t for t in old if t.get("id")}
    for t in new:
        tid = t.get("id")
        if not tid:
            continue
        prev = by_id.get(tid)
        if not prev or len(t.get("subComments") or []) >= len(prev.get("subComments") or []):
            by_id[tid] = t
    # keep original order, then append new ids
    out = []
    seen = set()
    for t in old + new:
        tid = t.get("id")
        if tid and tid not in seen and tid in by_id:
            out.append(by_id[tid])
            seen.add(tid)
    return out


def main() -> None:
    incoming = []
    if len(sys.argv) > 1:
        incoming = load_json(Path(sys.argv[1]))
    old = load_json(THREADS)
    merged = merge(old, incoming)
    THREADS.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"merged {len(incoming)} -> {len(merged)} threads")


if __name__ == "__main__":
    main()
