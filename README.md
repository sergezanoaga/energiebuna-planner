# Energie Bună Planner

Internal publishing tool of Energie Bună (energiebuna.md), self-hosted at https://planner.energiebuna.md.

Based on [Postiz](https://github.com/gitroomhq/postiz-app) (AGPL-3.0), version in `VERSION`, modified by Energie Bună:
Energie Bună brand mark, name and colors instead of the Postiz ones, a brand panel on the sign-in page,
the sign-in cookie bound to the planner host. The full modification is `rebrand.py` with the files in `assets/`;
applied to the upstream tag it gives the exact source of the running image. License: AGPL-3.0, as upstream.

## Как устроено (для своих)

- `VERSION`: версия Postiz (`UPSTREAM`) и номер нашей переделки (`REV`).
- `rebrand.py <исходник Postiz>`: вся переделка. Каждая правка ищет точное место и падает, если его нет;
  в конце проверяет, что в надписях не осталось «Postiz» и фиолетового.
- `assets/`: знак, значки, узор и два компонента интерфейса. Собираются `python3 tools/gen.py` и `python3 tools/raster.py`
  из контуров сайта (`tools/znak-data.json` = `site/src/lib/znak-data.json`).
- Сборка на GitHub при каждом пуше в `main`: образ `ghcr.io/sergezanoaga/energiebuna-planner:<UPSTREAM>-<REV>`.
- На сервере образ подставляется в `/opt/postiz/docker-compose.yml` вместо `gitroomhq/postiz-app`.
  Откат: вернуть `ghcr.io/gitroomhq/postiz-app:<UPSTREAM>` и `docker compose up -d`, база та же.

Новая версия Postiz: поменять `UPSTREAM`, сбросить `REV` на `eb1`, пуш. Если `rebrand.py` упал, место правки в Postiz сдвинулось.
