#!/usr/bin/env python3
"""Переодевает исходник Postiz в Energie Bună Planner.

Запуск: python3 rebrand.py <папка исходника Postiz нужной версии>
Ничего не угадывает: каждая правка ищет точное место и падает, если его нет,
чтобы новая версия Postiz не собралась молча наполовину переодетой.
"""
import colorsys
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
    "622ff6": "C2410C",
    "d82d7e": "A5360A",
    "ff3ea2": "DD5E2C",
}
# Всё остальное фиолетовое и малиновое в интерфейсе: тот же цвет, но с оттенком кирпичного (светлота и насыщенность свои).
BRICK_HUE = colorsys.rgb_to_hls(0xC2 / 255, 0x41 / 255, 0x0C / 255)[0]
# Цвета чужих брендов, которые должны остаться своими: фоны постов Facebook, знак Farcaster.
HUE_KEEP = {
    "apps/frontend/src/components/new-launch/providers/facebook/facebook.background.ts",
    "apps/frontend/src/components/auth/providers/farcaster.provider.tsx",
}


def is_violet(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return 250 <= h * 360 <= 345 and s > 0.3 and v > 0.2


def to_brick(r, g, b):
    _, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return [round(x * 255) for x in colorsys.hls_to_rgb(BRICK_HUE, l, s)]


def shift_hex(m):
    h = m.group(2)
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    if not is_violet(*rgb):
        return m.group(0)
    return m.group(1) + "%02X%02X%02X" % tuple(to_brick(*rgb))


def shift_rgb(m):
    rgb = [int(x) for x in m.group(2, 3, 4)]
    if not is_violet(*rgb):
        return m.group(0)
    return m.group(1) + "%d, %d, %d" % tuple(to_brick(*rgb))


HEX_RE = re.compile(r"(#|%23)([0-9a-fA-F]{6})(?![0-9a-fA-F])")
RGB_RE = re.compile(r"(rgba?\()(\d+),\s*(\d+),\s*(\d+)")


def violet_left(text):
    for m in HEX_RE.finditer(text):
        h = m.group(2)
        if is_violet(*[int(h[i:i + 2], 16) for i in (0, 2, 4)]):
            yield m.group(0)
    for m in RGB_RE.finditer(text):
        if is_violet(*[int(x) for x in m.group(2, 3, 4)]):
            yield m.group(0)
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

    # 4a. Помощник CopilotKit (кнопка чата в окне поста) и пункт «Agent» в меню: ключа нейросети нет, подпись чужая.
    modal = fe / "src/components/new-launch/manage.modal.tsx"
    replace_once(modal, r"\n\s*<CopilotPopup\b.*?/>", "", re.S)
    replace_once(modal, r"import \{ CopilotPopup \} from '@copilotkit/react-ui';\n", "")
    replace_once(
        fe / "src/components/layout/top.menu.tsx",
        r"\{\s*name: 'Agent',.*?path: '/agents',\s*\},\s*",
        "",
        re.S,
    )

    # 4b. Номер версии Postiz внизу колонки каналов.
    replace_once(
        fe / "src/components/launches/launches.component.tsx",
        r"<div>\s*\{process\.env\.NEXT_PUBLIC_VERSION\s*\?\s*process\.env\.NEXT_PUBLIC_VERSION\s*:\s*''\}\s*</div>",
        "",
    )

    # 4c. Огонёк серии публикаций в шапке.
    lay = fe / "src/components/new-layout/layout.component.tsx"
    replace_once(lay, r'<StreakComponent />\s*<div className="w-\[1px\] h-\[20px\] bg-blockSeparator mobile:hidden" />\s*', "")
    replace_once(lay, r"import \{ StreakComponent \}[^\n]*\n", "")

    # 4d. Страница входа: без кнопок чужих входов (Google не настроен) и без ссылки на регистрацию (она закрыта).
    login = fe / "src/components/auth/login.tsx"
    replace_once(
        login,
        r'<div className="text-\[14px\] mt-\[32px\] mb-\[12px\]">\s*\{t\(\'continue_with\'.*?\{t\(\'or\', \'or\'\)\}</div>\s*</div>\s*</div>',
        '<div className="flex flex-col mt-[32px]">',
        re.S,
    )
    replace_once(login, r'<p className="mt-4 text-sm">\s*\{t\(\'don_t_have_an_account\'.*?</p>\s*', "", re.S)

    # 4e. TikTok: видимость ролика выбирает человек, заранее ничего не стоит (правило TikTok для прямой публикации).
    replace_once(
        fe / "src/components/new-launch/providers/tiktok/tiktok.provider.tsx",
        r"\{\.\.\.register\('privacy_level', \{\s*value: 'PUBLIC_TO_EVERYONE',\s*\}\)\}",
        "{...register('privacy_level')}",
    )
    # Если видимость всё же пришла пустой, ролик уходит закрытым, а не всем.
    for f in ("tiktok.provider.ts", "tiktok.business.provider.ts"):
        replace_once(
            src / "libraries/nestjs-libraries/src/integrations/social" / f,
            r"privacy_level \|\| 'PUBLIC_TO_EVERYONE'",
            "privacy_level || 'SELF_ONLY'",
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
        if str(p.relative_to(src)) not in HUE_KEEP:
            new = HEX_RE.sub(shift_hex, new)
            new = RGB_RE.sub(shift_rgb, new)
        if new != t:
            p.write_text(new, errors="surrogateescape")
            recolored += 1

    # 7. Проверка: в надписях не осталось ни Postiz, ни фиолетового.
    left = [str(p.relative_to(src)) for p in files(src, TEXT_DIRS, TEXT_EXT) if "Postiz" in p.read_text()]
    purple = [
        str(p.relative_to(src))
        for p in files(src, COLOR_DIRS, COLOR_EXT)
        if str(p.relative_to(src)) not in HUE_KEEP
        and next(violet_left(p.read_text(errors="surrogateescape")), None)
    ]
    if left or purple:
        fail(f"осталось Postiz: {left[:10]}, фиолетовый: {purple[:10]}")
    print(f"готово: надписи в {renamed} файлах, цвета в {recolored} файлах, знак и страница входа заменены")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
