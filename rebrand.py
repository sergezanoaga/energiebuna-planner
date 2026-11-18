#!/usr/bin/env python3
"""Переодевает исходник Postiz в Energie Bună Planner.

Запуск: python3 rebrand.py <папка исходника Postiz нужной версии>
Ничего не угадывает: каждая правка ищет точное место и падает, если его нет,
чтобы новая версия Postiz не собралась молча наполовину переодетой.
"""
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = "Energie Bună Planner"

# Каталоги, где живут видимые человеку надписи (интерфейс и ответы сервера).
TEXT_DIRS = [
    "apps/frontend/src",
    "apps/backend/src",
    "apps/orchestrator/src",
    "libraries/nestjs-libraries/src",
    "libraries/helpers/src",
    "libraries/react-shared-libraries/src",
]
TEXT_EXT = {".ts", ".tsx", ".json"}

# Фиолетовая гамма Postiz → кирпичная гамма Energie Bună (site/src/styles: brand-300/500/600).
COLORS = {
    "612bd3": "C2410C",
    "612ad5": "C2410C",
    "4f46e5": "C2410C",
    "5520cb": "A5360A",
    "ae8afc": "DD5E2C",
    "b69dec": "DD5E2C",
    "fc69ff": "DD5E2C",
}
COLOR_DIRS = ["apps/frontend/src", "libraries/react-shared-libraries/src", "apps/frontend/public"]
COLOR_EXT = {".ts", ".tsx", ".scss", ".css", ".svg"}

AUTH_PANEL = """<div
          className="flex-1 hidden lg:flex items-center justify-center rounded-[12px]"
          style={{ backgroundColor: '#C2410C', backgroundImage: "url('/eb-pattern.svg')", backgroundSize: '221px 212px' }}
        >
          <div className="bg-[#C2410C] px-[56px] py-[48px] rounded-[24px]">
            <img src="/eb-stacked.svg" alt="Energie Bună" className="w-[340px] block" />
          </div>
        </div>"""


def fail(msg):
    sys.exit(f"ОСТАНОВКА: {msg}")


def files(src, dirs, exts):
    for d in dirs:
        base = src / d
        if not base.is_dir():
            fail(f"нет каталога {d}")
        for p in base.rglob("*"):
            if p.is_file() and p.suffix in exts and "node_modules" not in p.parts:
                yield p


def replace_once(path, pattern, repl, flags=0):
    text = path.read_text()
    new, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        fail(f"не нашёл место правки в {path}")
    path.write_text(new)


def main(src):
    src = Path(src).resolve()
    fe = src / "apps/frontend"

    # 1. Картинки: знак, текстовый знак, значки вкладки, узор и знак для страницы входа.
    for f in (HERE / "assets/public").iterdir():
        shutil.copy2(f, fe / "public" / f.name)

    # 2. Знак в боковой панели и текстовый знак на странице входа.
    for name, dest in [
        ("logo.tsx", "src/components/new-layout/logo.tsx"),
        ("logo-text.component.tsx", "src/components/ui/logo-text.component.tsx"),
    ]:
        if not (fe / dest).is_file():
            fail(f"нет файла {dest}")
        shutil.copy2(HERE / "assets/src" / name, fe / dest)

    # 3. Страница входа: правая половина с «20 000 предпринимателей» и отзывами → панель бренда.
    auth = fe / "src/app/(app)/auth/layout.tsx"
    replace_once(
        auth,
        r'<div className="text-\[36px\] flex-1 pt-\[88px\][^"]*">.*?<TestimonialComponent />\s*</div>',
        AUTH_PANEL,
        re.S,
    )
    replace_once(auth, r"import \{ TestimonialComponent \}[^\n]*\n", "")

    # 4. Вход привязан к самому адресу, а не ко всему домену energiebuna.md.
    replace_once(
        src / "libraries/helpers/src/subdomain/subdomain.management.ts",
        r"return url\.domain! \? '\.' \+ url\.domain! : url\.hostname!;",
        "return url.hostname!;",
    )

    # 5. Слово Postiz в надписях → Energie Bună Planner.
    renamed = 0
    for p in files(src, TEXT_DIRS, TEXT_EXT):
        t = p.read_text()
        if "Postiz" in t:
            p.write_text(t.replace("Postiz", NAME))
            renamed += 1

    # 6. Цвета.
    recolored = 0
    for p in files(src, COLOR_DIRS, COLOR_EXT):
        t = p.read_text(errors="surrogateescape")
        new = t
        for old, col in COLORS.items():
            # и в обычной записи, и в закодированной внутри картинок data:url (%23 вместо #)
            new = re.sub("(#|%23)" + old, lambda m: m.group(1) + col, new, flags=re.I)
        new = re.sub(r"rgba?\(97, ?43, ?211", lambda m: m.group(0).split("(")[0] + "(194, 65, 12", new)
        if new != t:
            p.write_text(new, errors="surrogateescape")
            recolored += 1

    # 7. Проверка: в надписях не осталось ни Postiz, ни фиолетового.
    left = [str(p.relative_to(src)) for p in files(src, TEXT_DIRS, TEXT_EXT) if "Postiz" in p.read_text()]
    purple = [
        str(p.relative_to(src))
        for p in files(src, COLOR_DIRS, COLOR_EXT)
        if re.search("612bd3", p.read_text(errors="surrogateescape"), re.I)
    ]
    if left or purple:
        fail(f"осталось Postiz: {left[:10]}, фиолетовый: {purple[:10]}")
    print(f"готово: надписи в {renamed} файлах, цвета в {recolored} файлах, знак и страница входа заменены")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
