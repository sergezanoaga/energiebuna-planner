#!/usr/bin/env python3
"""Собирает файлы знака Energie Bună для планировщика из контуров сайта.

Источник контуров: tools/znak-data.json (копия site/src/lib/znak-data.json,
принятый файл Figma от 14.09.2026). Запуск: python3 tools/gen.py
Пишет в assets/public (картинки) и assets/src (компоненты интерфейса).
Значки PNG и favicon.ico рисует chromium, если он есть (tools/raster.sh).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "tools/znak-data.json").read_text())
PUB = ROOT / "assets/public"
SRC = ROOT / "assets/src"

BRICK, DARK, CREAM, BRICK_LIGHT = "#C2410C", "#201A15", "#FAF6F0", "#DD5E2C"
ZNACHOK_W, ZNACHOK_H = 83.77, 87.69  # только дуга и круг из формы stacked


def paths(form, rezhim, only=None, jsx=False):
    f = DATA["forms"][form]
    colors = DATA["rezhim"][rezhim]
    out = []
    for p in f["parts"]:
        if only and p["role"] not in only:
            continue
        fill = colors.get(p["role"], colors["letter"])
        out.append(f'<path d="{p["d"]}" fill="{fill}" />' if jsx else f'<path d="{p["d"]}" fill="{fill}"/>')
    return f, "".join(out) if not jsx else "\n        ".join(out)


def mark_group(size, box, rezhim, jsx=False):
    """Дуга и круг, вписанные по высоте в долю box от квадрата size."""
    f, body = paths("stacked", rezhim, {"arc", "disc"}, jsx)
    s = size * box / ZNACHOK_H
    x = (size - ZNACHOK_W * s) / 2
    y = (size - ZNACHOK_H * s) / 2
    return f'<g transform="translate({x:.2f} {y:.2f}) scale({s:.4f}) translate({f["tx"]} {f["ty"]})">{body}</g>'


def svg_mark(size=60, radius=14, box=0.5):
    g = mark_group(size, box, "brick")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">'
            f'<rect width="{size}" height="{size}" rx="{radius}" fill="{BRICK}"/>{g}</svg>\n')


def svg_form(form, rezhim, height):
    f, body = paths(form, rezhim)
    w = round(height * f["w"] / f["h"], 2)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{height}" viewBox="0 0 {f["w"]} {f["h"]}">'
            f'<g transform="translate({f["tx"]} {f["ty"]})">{body}</g></svg>\n')


def tsx_logo():
    g = mark_group(60, 0.5, "brick", jsx=True)
    return f"""'use client';

// Energie Bună: знак в боковой панели (вместо знака Postiz). Собрано tools/gen.py.
export const Logo = () => {{
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="60"
      height="60"
      viewBox="0 0 60 60"
      fill="none"
      className="mt-[8px] min-w-[60px] min-h-[60px]"
      role="img"
      aria-label="Energie Bună Planner"
    >
      <rect width="60" height="60" rx="14" fill="{BRICK}" />
      {g}
    </svg>
  );
}};
"""


def tsx_logo_text():
    f, body = paths("line", "dark", jsx=True)
    h = 34
    w = round(h * f["w"] / f["h"], 2)
    return f"""import React from 'react';

// Energie Bună Planner: знак строкой и подпись (вместо текстового знака Postiz). Собрано tools/gen.py.
export const LogoTextComponent = () => {{
  return (
    <div className="flex items-end gap-[12px]" aria-label="Energie Bună Planner">
      <svg
        width="{w}"
        height="{h}"
        viewBox="0 0 {f['w']} {f['h']}"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        role="img"
        aria-hidden="true"
      >
        <g transform="translate({f['tx']} {f['ty']})">
        {body}
        </g>
      </svg>
      <span className="text-[20px] leading-[1] font-[500] text-[{BRICK_LIGHT}] pb-[2px]">Planner</span>
    </div>
  );
}};
"""


def main():
    PUB.mkdir(parents=True, exist_ok=True)
    SRC.mkdir(parents=True, exist_ok=True)
    mark = svg_mark()
    for name in ("postiz.svg", "logo.svg", "eb-mark.svg"):
        (PUB / name).write_text(mark)
    line = svg_form("line", "dark", 61.24)
    for name in ("logo-text.svg", "postiz-text.svg"):
        (PUB / name).write_text(line)
    (PUB / "eb-stacked.svg").write_text(svg_form("stacked", "brick", 96))
    # квадрат без скругления, как значок приложения в TikTok: для растровых значков
    (ROOT / "tools/icon-square.svg").write_text(svg_mark(512, 0, 0.5))
    (SRC / "logo.tsx").write_text(tsx_logo())
    (SRC / "logo-text.component.tsx").write_text(tsx_logo_text())
    print("готово:", ", ".join(sorted(p.name for p in PUB.iterdir())), "|", ", ".join(sorted(p.name for p in SRC.iterdir())))


if __name__ == "__main__":
    main()
