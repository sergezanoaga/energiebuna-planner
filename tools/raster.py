#!/usr/bin/env python3
"""Растровые значки из tools/icon-square.svg через chromium: favicon.ico (16+32), favicon.png (32), postiz-fav.png (192)."""
import struct, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "tools/icon-square.svg"
PUB = ROOT / "assets/public"

def shot(size):
    with tempfile.TemporaryDirectory() as d:
        html = Path(d) / "i.html"
        html.write_text(f'<html><body style="margin:0"><img src="{SVG.as_uri()}" style="display:block;width:{size}px;height:{size}px"></body></html>')
        out = Path(d) / "o.png"
        subprocess.run(["chromium", "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                        "--allow-file-access-from-files", f"--window-size={size},{size}",
                        f"--screenshot={out}", html.as_uri()], check=True, capture_output=True)
        return out.read_bytes()

def ico(pngs):
    head = struct.pack("<HHH", 0, 1, len(pngs))
    off = 6 + 16 * len(pngs)
    entries, data = b"", b""
    for size, png in pngs:
        entries += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(png), off + len(data))
        data += png
    return head + entries + data

p16, p32, p192 = shot(16), shot(32), shot(192)
(PUB / "favicon.png").write_bytes(p32)
(PUB / "postiz-fav.png").write_bytes(p192)
(PUB / "favicon.ico").write_bytes(ico([(16, p16), (32, p32)]))
print("значки готовы")
