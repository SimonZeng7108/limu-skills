"""Save a CDP Page.captureScreenshot JSON (base64 PNG) to screenshots/."""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "screenshots"


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: save_cdp_png.py <cdp-json> <out-name.png>")
    src = Path(sys.argv[1])
    payload = json.loads(src.read_text(encoding="utf-8"))
    data = payload.get("data") or payload.get("result", {}).get("data")
    if not data:
        raise SystemExit(f"no image data in {src}")
    SHOTS.mkdir(parents=True, exist_ok=True)
    out = SHOTS / sys.argv[2]
    out.write_bytes(base64.b64decode(data))
    print(str(out).encode("utf-8", "backslashreplace").decode("ascii", "ignore"))


if __name__ == "__main__":
    main()
