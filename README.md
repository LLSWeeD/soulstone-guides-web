# Soulstone Guides

Статический сайт с карточками персонажей Soulstone Survivors (версия игры 1.5d): данные вики, актуальные и старые гайды, сверка утверждений гайдов с вики, советы по забегу, справочник навыков, пассивок и рун, общий гайд по механикам. RU/EN.

Личный проект. Тексты сторонних гайдов пересказаны со ссылками на источники. Данные вики — [Soulstone Survivors Wiki](https://soulstone-survivors.fandom.com/) (CC BY-SA). Иконки — графика игры, принадлежат её разработчику.

## Сборка

Нужен только Python 3 (без сторонних библиотек).

```bash
python scripts/validate.py      # проверка карточек data/characters/*.json
python scripts/build_site.py    # сборка сайта в dist/
```

Сайт открывается из `dist/index.html`. При пуше в `main` GitHub Actions проверяет карточки, собирает сайт и публикует его на GitHub Pages (`.github/workflows/pages.yml`).

## Устройство

- `data/characters/<Id>.json` — карточки персонажей (схема: `schema/character-card.schema.json`).
- `data/reference/` — справочник из вики (навыки, пассивки, руны, оружие, персонажи, иконки).
- `data/common/general.json` — общий гайд.
- `data/glossary.md` — русские названия из файлов игры.
- `site/` — стили, скрипт и иконки сайта.
- `scripts/` — выкачка (`fetch_all.py`, `fetch_icons.py`), очистка (`clean.py`), справочник (`build_reference.py`), проверки (`validate.py`, `check_weapons.py`), инструменты для сверки (`lookup.py`, `describe.py`), сборка сайта (`build_site.py`).
- `TZ.md` — техзадание, `NOTES.md` — журнал работы и открытые вопросы.

Выкачанные исходники (`raw/`, `clean/`) и рабочие файлы агентов (`work/`) в репозиторий не входят: их можно получить заново скриптами `fetch_all.py` и `clean.py`.
