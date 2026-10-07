"""Сборка статического сайта: data/ -> dist/. Без ИИ и сторонних зависимостей.

Запуск: python scripts/build_site.py
Результат открывается локально (dist/index.html) и разворачивается на GitHub Pages как есть.
Страницы: главная со всеми персонажами + страница на каждого персонажа. Карточка
(data/characters/<Id>.json) добавляет гайды; без неё страница показывает только данные вики.
"""
import html
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_reference import load_glossary, ru_lookup  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "data" / "reference"
CARDS = ROOT / "data" / "characters"
ASSETS = ROOT / "site"
DIST = ROOT / "dist"
GAME_VERSION = "1.5d"

import hashlib  # noqa: E402

GL = load_glossary()
# метка версии стилей и скрипта: браузер не возьмёт устаревшую копию из кэша после пересборки
ASSET_VER = hashlib.sha1(b"".join((ASSETS / f).read_bytes() for f in ("style.css", "app.js"))).hexdigest()[:8]
REFS = {n: {x["id"]: x for x in json.loads((REF / f"{n}.json").read_text(encoding="utf-8"))}
        for n in ("characters", "weapons", "skills", "powers", "runes")}

ICON_FILE = REF / "icons.json"
ICONS = json.loads(ICON_FILE.read_text(encoding="utf-8")) if ICON_FILE.exists() else {}
UP = ""  # относительный путь к корню сайта для страницы, которую собираем сейчас

RARITY = {"R1": ("common", "Обычное", "Common"), "R2": ("uncommon", "Необычное", "Uncommon"),
          "R3": ("rare", "Редкое", "Rare"), "R4": ("epic", "Эпическое", "Epic"),
          "R5": ("legendary", "Легендарное", "Legendary")}
ROLE = {"core": ("Ядро", "Core"), "damage": ("Урон", "Damage"), "support": ("Поддержка", "Support"),
        "optional": ("Опционально", "Optional")}
PRIORITY = {"must": ("Обязательно", "Must"), "high": ("Высокий", "High"), "medium": ("Средний", "Medium"),
            "situational": ("По ситуации", "Situational")}
ARCHETYPE = {"stack": ("Стаки", "Stack"), "multiplier": ("Множители", "Multiplier"), "dot": ("DoT", "DoT"),
             "summon": ("Призыв", "Summon"), "generalist": ("Generalist", "Generalist"),
             "synchrony": ("Synchrony", "Synchrony"), "other": ("Другое", "Other")}
STATUS = {"verified": ("Проверено", "Verified", "✓"), "conflict": ("Расхождение", "Conflict", "!"),
          "unverified": ("Не проверено", "Unverified", "?")}
IMPACT = {"broken": ("Сломано", "Broken"), "weakened": ("Ослаблено", "Weakened"),
          "unchanged": ("Без изменений", "Unchanged"), "buffed": ("Усилено", "Buffed"),
          "unknown": ("Неясно", "Unclear")}
CONFIDENCE = {"high": ("высокая", "high"), "medium": ("средняя", "medium"), "low": ("низкая", "low"),
              "unconfirmed": ("не подтверждено", "unconfirmed")}
SOURCE_BY = {"wiki": ("по вики", "per wiki"), "game": ("в игре", "in game"), "user": ("проверено вручную", "checked by hand")}


def e(s):
    return html.escape(str(s or ""), quote=True)


def bi(ru, en, tag="span", cls=""):
    """Двуязычный текст: оба варианта в разметке, видимость переключает CSS."""
    ru, en = ru or en, en or ru
    c = f' class="{cls}"' if cls else ""
    if ru == en:
        return f"<{tag}{c}>{e(ru)}</{tag}>"
    return f'<{tag}{c}><span class="ru">{e(ru)}</span><span class="en">{e(en)}</span></{tag}>'


def txt(t, tag="span", cls=""):
    """Поле схемы {ru, en}."""
    if not t:
        return ""
    return bi(t.get("ru"), t.get("en"), tag, cls)


def pair(d):
    return bi(d[0], d[1])


def ent_name(x):
    """Название игровой сущности: RU (EN мелко), в режиме EN только EN."""
    en, ru = x.get("name_en", x.get("id")), x.get("name_ru")
    if not ru or ru == en:
        return e(en)
    return f'<span class="ru">{e(ru)} <small class="orig">{e(en)}</small></span><span class="en">{e(en)}</span>'


def ico(kind, eid, size="s"):
    """Иконка сущности; если её нет, пустое место того же размера, чтобы строки не ехали."""
    rel = ICONS.get(kind, {}).get(eid)
    if not rel:
        return f'<span class="ico ico-{size} ph"></span>'
    return f'<img class="ico ico-{size}" src="{UP}assets/{rel}" alt="" loading="lazy">'


STAT_ALIAS = {"Maximum Health": "Max Health", "Crit Damage Chance": "Critical Chance",
              "Area Modifer": "Area Modifier", "Experiece": "Experience"}  # разнобой и опечатки вики


def stat_name(name):
    ru = ru_lookup(GL, STAT_ALIAS.get(name, name), ["Характеристики"])
    return bi(ru, name) if ru else e(name)


def stat_chips(stats):
    out = []
    for s in stats:
        v = str(s.get("value", ""))
        sign = "pos" if v.startswith("+") else "neg" if v.startswith("-") else ""
        out.append(f'<li class="stat {sign}"><b>{e(v)}</b> {stat_name(s["name"])}</li>')
    return f'<ul class="stats">{"".join(out)}</ul>' if out else ""


def chips(items, cls="chip"):
    return "".join(f'<span class="{cls}">{i}</span>' for i in items)


def skill_ref(sid):
    s = REFS["skills"].get(sid)
    if not s:
        return e(sid)
    tip = e(s["description"])
    types = " · ".join(s["skill_types"])
    return (f'{ico("skills", sid)}<a class="ent" href="{UP}ref/skills.html#s-{sid}" '
            f'title="{tip}&#10;[{e(types)}]">{ent_name(s)}</a>')


def rune_ref(r):
    rr = REFS["runes"].get(r["id"])
    if not rr:
        return e(r["id"])
    name = rr["name_en"] + (f": {r['variant']}" if r.get("variant") else "")
    tip = rr.get("description") or (rr["variants"].get(r.get("variant"), {}).get("unlock") if rr.get("family") else "")
    eid = r["id"] + ("_" + r["variant"] if r.get("variant") else "")
    return f'{ico("runes", eid)}<a class="ent" href="{UP}ref/runes.html#r-{r["id"]}" title="{e(tip)}">{e(name)}</a>'


def power_ref(p):
    if p.get("power_id"):
        pw = REFS["powers"].get(p["power_id"], {"name_en": p["power_id"]})
        name = ent_name(pw)
        if p.get("variant"):
            name += f' <span class="variant">{e(p["variant"])}</span>'
        tip = pw.get("description") or ("Есть в игре, описания на вики нет" if pw.get("source") == "game-glossary" else "")
        return (f'{ico("powers", p["power_id"])}<a class="ent" href="{UP}ref/powers.html#p-{p["power_id"]}" '
                f'title="{e(tip)}">{name}</a>')
    if p.get("power_name"):
        return f'{ico("powers", "")}<span class="ent unknown" title="Нет на вики">{e(p["power_name"])}</span>'
    return f'{ico("powers", "")}<span class="ent stat-ref">{stat_name(p["stat"])}</span>'


# ---------- разметка страниц ----------
def page(title, body, depth=0, desc=""):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="ru" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="stylesheet" href="{up}assets/style.css?v={ASSET_VER}">
<script>try{{var l=localStorage.getItem('lang');if(l)document.documentElement.dataset.lang=l;var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t}}catch(_){{}}</script>
</head>
<body>
<header class="top">
  <a class="brand" href="{up}index.html">Soulstone <span>Guides</span></a>
  <span class="ver">v{GAME_VERSION}</span>
  <nav class="mainnav">
    <a href="{up}index.html">{bi("Персонажи", "Characters")}</a>
    <a href="{up}ref/skills.html">{bi("Справочник", "Reference")}</a>
    <a href="{up}general.html">{bi("Общий гайд", "General guide")}</a>
  </nav>
  <div class="tools">
    <button class="tbtn" data-act="lang" aria-label="Язык / Language"><span class="ru">EN</span><span class="en">RU</span></button>
    <button class="tbtn" data-act="theme" aria-label="Тема / Theme">◐</button>
  </div>
</header>
<main>
{body}
</main>
<footer class="foot">
  {bi("Данные: ", "Data: ")}<a href="https://soulstone-survivors.fandom.com/" rel="noopener">Soulstone Survivors Wiki</a> (CC BY-SA),
  <a href="https://cubiccreativity.wordpress.com/" rel="noopener">cubiccreativity</a>,
  <a href="https://steamcommunity.com/sharedfiles/filedetails/?id=3251066730" rel="noopener">Steam guide</a>.
  {bi("Тексты гайдов пересказаны, не скопированы. Личный проект.", "Guide texts are paraphrased, not copied. Personal project.")}
</footer>
<script src="{up}assets/app.js?v={ASSET_VER}"></script>
</body>
</html>
"""


def guide_status(card):
    if not card:
        return "none", ("Только вики", "Wiki only")
    kinds = {g["kind"] for g in card["guides"]}
    if "current" in kinds:
        return "current", (f"Гайд {GAME_VERSION}", f"Guide {GAME_VERSION}")
    if "legacy" in kinds:
        return "legacy", ("Только старый гайд", "Old guide only")
    return "none", ("Только вики", "Wiki only")


def load_cards():
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in CARDS.glob("*.json")}


def build_index(cards):
    global UP
    UP = ""
    tiles, classes = [], set()
    for c in sorted(REFS["characters"].values(), key=lambda x: x["name_en"]):
        cls = [x.strip() for x in c["class"].split(",") if x.strip()]
        classes |= set(cls)
        st, label = guide_status(cards.get(c["id"]))
        search = " ".join(filter(None, [c["name_en"], c.get("name_ru"), *c["skill_types"], *cls])).lower()
        tiles.append(f"""
<a class="tile" href="c/{c['id']}.html" data-class="{e('|'.join(cls))}" data-search="{e(search)}">
  <span class="badge {st}">{pair(label)}</span>
  {ico("characters", c["id"], "l")}
  <h2>{ent_name(c)}</h2>
  <p class="meta">{e(c['class'])} · {e(c['weapon_type'])}</p>
  <div class="types">{chips(e(t) for t in c['skill_types'])}</div>
</a>""")
    filters = "".join(f'<button class="fbtn" data-class="{e(x)}">{e(x)}</button>' for x in sorted(classes))
    body = f"""
<section class="hero">
  <h1>{bi("Персонажи", "Characters")}</h1>
  <p class="lead">{bi("Карточки персонажей: данные вики, актуальные билды и старые гайды с пометками, что устарело.",
                       "Character cards: wiki data, current builds and old guides flagged for what changed.")}</p>
  <div class="filters">
    <input id="q" type="search" placeholder="Поиск / Search" aria-label="Поиск">
    <button class="fbtn on" data-class="">{bi("Все", "All")}</button>{filters}
  </div>
</section>
<section class="promo">
  <a class="promo-card" href="general.html"><b>{bi("Общий гайд", "General guide")}</b>
    <span>{bi("Главное правило игры: пассивки зависят от того, что уже есть. Архетипы, цепочки эффектов, порядок забега.",
              "The core rule: powers depend on what you have. Archetypes, effect chains, run order.")}</span></a>
  <a class="promo-card" href="ref/skills.html"><b>{bi("Справочник", "Reference")}</b>
    <span>{bi("Навыки, пассивки и руны с описаниями вики и списком персонажей, у кого они в билдах.",
              "Skills, powers and runes with wiki descriptions and which characters use them.")}</span></a>
</section>
<section class="grid" id="grid">{''.join(tiles)}</section>
<p class="empty" id="empty" hidden>{bi("Ничего не найдено", "Nothing found")}</p>"""
    return page("Soulstone Survivors — гайды", body, 0, "Карточки персонажей Soulstone Survivors")


def weapon_block(c):
    have = {REFS["weapons"][w]["rarity"]: REFS["weapons"][w] for w in c["weapons"] if w in REFS["weapons"]}
    rarities = ["R1"] if c["id"] == "Blacksmith" else list(RARITY)
    out = []
    for r in rarities:
        cls, ru, en = RARITY[r]
        w = have.get(r)
        if not w:
            out.append(f'<article class="weapon {cls} missing"><p class="rar">{bi(ru, en)}</p>'
                       f'<p class="muted">{bi("Нет данных на вики", "Not on the wiki")}</p></article>')
            continue
        skills = ", ".join(skill_ref(s) for s in w["skills"])
        ap = ""
        if w.get("artifact_power"):
            ap = (f'<p class="ap" title="{e(w["artifact_power_description"])}"><b>{bi("Сила артефакта", "Artifact Power")}:</b> '
                  f'{e(w["artifact_power"])}</p>')
        out.append(f"""<article class="weapon {cls}">
  <p class="rar">{bi(ru, en)} · {e(w['skill_type'])}</p>
  <h3>{ico("weapons", w["id"], "m")}{ent_name(w)}</h3>
  {stat_chips(w['stats'])}
  <p class="wskills"><b>{bi("Навыки", "Skills")}:</b> {skills}</p>
  {ap}
</article>""")
    return f'<section class="block"><h2>{bi("Оружие", "Weapons")}</h2><div class="weapons">{"".join(out)}</div></section>'


def claims_block(claims):
    if not claims:
        return ""
    rows = []
    for x in claims:
        ru, en, icon = STATUS[x["status"]]
        by = f' · {pair(SOURCE_BY[x["verified_by"]])}' if x.get("verified_by") else ""
        detail = f'<p class="detail">{e(x["detail"])}</p>' if x.get("detail") else ""
        rows.append(f'<li class="claim {x["status"]}"><span class="st" title="{e(ru)}">{icon}</span>'
                    f'<div>{txt(x["text"], "p")}<p class="cmeta">{bi(ru, en)}{by}</p>{detail}</div></li>')
    return f'<div class="claims"><h4>{bi("Утверждения гайда", "Guide claims")}</h4><ul>{"".join(rows)}</ul></div>'


def build_view(b, c):
    w = REFS["weapons"].get(b.get("weapon_id") or "")
    weapon = ""
    if w:
        cls = RARITY.get(w["rarity"], ("common",))[0]
        weapon = f'<span class="wtag {cls}">{ico("weapons", w["id"])}{ent_name(w)}</span>'
    skills = "".join(
        f'<tr><td>{skill_ref(s["id"])}</td><td><span class="role {s["role"]}">{pair(ROLE[s["role"]])}</span></td>'
        f'<td>{txt(s.get("note"))}</td></tr>' for s in b["skills"])
    order = list(PRIORITY)
    passives = "".join(
        f'<li><span class="prio {p.get("priority", "situational")}">{pair(PRIORITY[p.get("priority", "situational")])}</span>'
        f'{power_ref(p)}{(" — " + txt(p["note"])) if p.get("note") else ""}</li>'
        for p in sorted(b.get("passives", []), key=lambda p: order.index(p.get("priority", "situational"))))
    runes = ""
    for slot, label in (("tenacity", ("Tenacity", "Tenacity")), ("versatility", ("Versatility", "Versatility"))):
        items = b["runes"].get(slot, [])
        lis = "".join(f"<li>{rune_ref(r)}</li>" for r in items) or f'<li class="muted">{bi("не указаны", "not listed")}</li>'
        runes += f'<div><h5>{pair(label)}</h5><ul class="runes">{lis}</ul></div>'
    legacy = ""
    if b.get("legacy_check"):
        rows = "".join(f'<tr><td>{e(x["mechanic"])}</td><td><span class="impact {x["impact"]}">{pair(IMPACT[x["impact"]])}</span></td>'
                       f'<td>{txt(x.get("note"))}</td></tr>' for x in b["legacy_check"])
        legacy = (f'<div class="legacy-check"><h4>{bi("Что изменилось к 1.5d", "What changed by 1.5d")}</h4>'
                  f'<table><tbody>{rows}</tbody></table></div>')
    conf = CONFIDENCE[b["confidence"]]
    return f"""
<div class="build">
  <div class="bhead">
    {weapon}
    {chips((pair(ARCHETYPE[a]) for a in b["archetypes"]), "chip arch")}
    <span class="conf">{bi("Уверенность", "Confidence")}: {pair(conf)}</span>
  </div>
  {txt(b.get("playstyle"), "p", "playstyle")}
  {f'<p class="core"><b>{bi("Ключевые механики", "Core mechanics")}:</b> {", ".join(e(m) for m in b["core_mechanics"])}</p>' if b.get("core_mechanics") else ""}
  <div class="cols">
    <div><h4>{bi("Навыки", "Skills")}</h4><table class="skills"><tbody>{skills}</tbody></table></div>
    <div>
      <h4>{bi("Пассивки", "Passives")}</h4><ul class="passives">{passives or '<li class="muted">—</li>'}</ul>
      <h4>{bi("Руны", "Runes")}</h4><div class="runecols">{runes}</div>
    </div>
  </div>
  {claims_block(b.get("claims"))}
  {legacy}
</div>"""


def guide_view(g, c, uid):
    tabs, panels = [], []
    for i, b in enumerate(g["builds"]):
        bid = f"{uid}-{i}"
        tabs.append(f'<button role="tab" class="tab{" on" if i == 0 else ""}" data-tab="{bid}">{txt(b["name"])}</button>')
        panels.append(f'<div class="panel" id="{bid}"{"" if i == 0 else " hidden"}>{build_view(b, c)}</div>')
    head = (f'<p class="src"><a href="{e(g["url"])}" rel="noopener">{e(g["title"])}</a> · '
            f'{bi("версия", "version")} {e(g["game_version"])} · {bi("обновлён", "updated")} {e(g["updated"])}</p>')
    note = f'<div class="note">{txt(g["legacy_note"], "p")}</div>' if g.get("legacy_note") else ""
    return f'{head}{note}<div class="tabs" role="tablist">{"".join(tabs)}</div>{"".join(panels)}'


def derived_view(d):
    if not d or not (d.get("banish") or d.get("level_up_rules")):
        return ""
    bans = "".join(f'<li><b>{e(x["target"])}</b> — {txt(x["reason"])}</li>' for x in d.get("banish", []))
    rules = "".join(f"<li>{txt(r)}</li>" for r in d.get("level_up_rules", []))
    return f"""<section class="block derived">
  <h2>{bi("Советы по забегу", "Run tips")}</h2>
  <p class="flag">{bi("Сведено вручную: часть советов взята из гайдов, часть выведена. Источник указан у каждого бана.",
                     "Compiled by hand: some tips come from guides, some are inferred. Each ban states its source.")}</p>
  <div class="cols">
    <div><h4>{bi("Что банить", "What to banish")}</h4><ul class="bans">{bans or '<li class="muted">—</li>'}</ul></div>
    <div><h4>{bi("При повышении уровня", "On level-up")}</h4><ol class="rules">{rules}</ol></div>
  </div>
  {txt(d.get("basis"), "p", "basis")}
</section>"""


def build_character(c, card):
    global UP
    UP = "../"
    st, label = guide_status(card)
    summary = txt(card.get("summary"), "p", "lead") if card else ""
    unique = ", ".join(skill_ref(s.replace(" ", "")) if s.replace(" ", "") in REFS["skills"] else e(s)
                       for s in c["starting_unique_skills"])
    facts = f"""<section class="block facts">
  <div class="cols">
    <div>
      <h4>{bi("Бонусы персонажа", "Character stats")}</h4>{stat_chips(c['stats'])}
      <h4>{bi("Типы навыков", "Skill types")}</h4><div class="types">{chips(e(t) for t in c['skill_types'])}</div>
    </div>
    <div>
      <dl class="kv">
        <dt>{bi("Класс", "Class")}</dt><dd>{e(c['class'])}</dd>
        <dt>{bi("Оружие", "Weapon type")}</dt><dd>{e(c['weapon_type'])}</dd>
        <dt>{bi("Как открыть", "Unlock")}</dt><dd>{e(c['unlock'])}</dd>
        {f'<dt>{bi("Уникальные навыки", "Unique skills")}</dt><dd>{unique}</dd>' if unique else ""}
        {f'<dt>{bi("Руны дерева", "Tree runes")}</dt><dd>{", ".join(e(r) for r in c["tree_runes"])}</dd>' if c["tree_runes"] else ""}
      </dl>
      <p class="src"><a href="{e(c['wiki_url'])}" rel="noopener">{bi("Страница на вики", "Wiki page")}</a></p>
    </div>
  </div>
</section>"""
    guides = ""
    if card:
        cur = [g for g in card["guides"] if g["kind"] == "current"]
        old = [g for g in card["guides"] if g["kind"] == "legacy"]
        for i, g in enumerate(cur):
            guides += f'<section class="block"><h2>{bi("Билды", "Builds")} <span class="badge current">{e(g["game_version"])}</span></h2>{guide_view(g, c, f"cur{i}")}</section>'
        if not cur:
            guides += (f'<section class="block warn"><p>{bi("Актуального гайда под " + GAME_VERSION + " нет. Ниже только старый гайд и выводы.", "No current " + GAME_VERSION + " guide. Only an old guide and inferences below.")}</p></section>')
        for i, g in enumerate(old):
            open_attr = "" if cur else " open"
            guides += (f'<details class="block legacy"{open_attr}><summary><h2>{bi("Старый гайд", "Old guide")} '
                       f'<span class="badge legacy">{bi("патч", "patch")} {e(g["game_version"])}</span></h2></summary>'
                       f'{guide_view(g, c, f"old{i}")}</details>')
        guides += derived_view(card.get("derived"))
        if card.get("gaps"):
            guides += (f'<details class="block gaps"><summary><h2>{bi("Пробелы в данных", "Data gaps")}</h2></summary>'
                       f'<ul>{"".join(f"<li>{e(x)}</li>" for x in card["gaps"])}</ul></details>')
    else:
        guides = f'<section class="block warn"><p>{bi("Карточка ещё не собрана: здесь пока только данные вики.", "Card not compiled yet: wiki data only.")}</p></section>'
    body = f"""
<nav class="crumbs"><a href="../index.html">{bi("Все персонажи", "All characters")}</a></nav>
<section class="hero char">
  <span class="badge {st}">{pair(label)}</span>
  <h1>{ico("characters", c["id"], "xl")}{ent_name(c)}</h1>
  {summary}
</section>
{facts}
{weapon_block(c)}
{guides}"""
    title = f"{c.get('name_ru') or c['name_en']} ({c['name_en']}) — Soulstone Survivors"
    return page(title, body, 1, f"Карточка персонажа {c['name_en']}")


# ---------- справочник ----------
USAGE = {"skills": {}, "runes": {}, "powers": {}}


def collect_usage(cards):
    for cid, card in cards.items():
        for g in card["guides"]:
            for b in g["builds"]:
                for x in b["skills"]:
                    USAGE["skills"].setdefault(x["id"], set()).add(cid)
                for slot in b["runes"].values():
                    for r in slot:
                        USAGE["runes"].setdefault(r["id"], set()).add(cid)
                for x in b.get("passives", []):
                    if x.get("power_id"):
                        USAGE["powers"].setdefault(x["power_id"], set()).add(cid)


def char_link(cid, up="../"):
    c = REFS["characters"].get(cid)
    if not c:
        return e(cid)
    return f'<a class="clink" href="{up}c/{cid}.html">{ico("characters", cid)}{bi(c.get("name_ru"), c["name_en"])}</a>'


REF_KINDS = [("skills", "s", ("Навыки", "Skills")), ("powers", "p", ("Пассивки", "Powers")),
             ("runes", "r", ("Руны", "Runes"))]


def ref_item(kind, prefix, x):
    tags, meta = [], []
    if kind == "skills":
        tags += x["skill_types"]
        meta.append(" · ".join(x["skill_types"]))
        if x.get("unlock"):
            meta.append(x["unlock"])
    elif kind == "runes":
        sec = "Family" if x.get("family") else (x.get("section") or "")
        tags.append(sec)
        if not x.get("family"):
            meta += [x.get("section") or "", f'{x.get("runic_power_cost")} RP', x.get("rarity") or "", x.get("skill_tree") or ""]
    else:
        src = "wiki" if x.get("description") else "game"
        tags.append(src)
        if x.get("rarities"):
            meta.append(", ".join(x["rarities"]))
    used = sorted(USAGE[kind].get(x["id"], []), key=lambda c: REFS["characters"][c]["name_en"])
    if used:
        tags.append("used")
    desc = x.get("description") or ""
    body = ""
    if desc:
        body += f'<p class="desc">{e(desc)}</p>'
    elif kind == "powers" and x.get("source") == "game-glossary":
        body += f'<p class="desc muted">{bi("Есть в файлах игры, описания и чисел на вики нет.", "In the game files; no wiki description or numbers.")}</p>'
    if x.get("note"):
        body += f'<p class="desc muted">{e(x["note"])}</p>'
    stats = x.get("stats") or []
    if stats:
        parts = []
        for st in stats:
            if "values" in st:
                vals = ", ".join(f"{k}: {v}" for k, v in st["values"].items() if v)
                parts.append(f'{e(st["name"])} <span class="muted">({e(vals)})</span>')
            else:
                parts.append(f'{e(st.get("Name"))} <b>{e(st.get("Value"))}</b>')
        body += f'<p class="rstats">{" · ".join(parts)}</p>'
    if kind == "runes" and x.get("family"):
        vs = "".join(f'<li>{ico("runes", x["id"] + "_" + v)}<b>{e(v)}</b> <span class="muted">— {e(d.get("character", ""))}: '
                     f'{e(d.get("unlock", ""))}</span></li>' for v, d in x["variants"].items())
        body += f'<ul class="variants">{vs}</ul>'
    if used:
        body += f'<p class="used"><b>{bi("В билдах", "In builds")}:</b> {" ".join(char_link(c) for c in used)}</p>'
    search = " ".join(filter(None, [x["name_en"], x.get("name_ru"), x["id"], desc, *tags])).lower()
    icon_id = x["id"]
    return f"""<article class="ritem" id="{prefix}-{e(x['id'])}" data-search="{e(search)}" data-tags="{e('|'.join(tags))}">
  <div class="rhead">{ico(kind, icon_id, "m")}<div><h3>{ent_name(x)}</h3>
  <p class="rmeta">{e(" · ".join(m for m in meta if m))}</p></div></div>
  {body}
</article>"""


def build_ref(kind, prefix, label):
    global UP
    UP = "../"
    items = sorted(REFS[kind].values(), key=lambda x: (x.get("source") == "game-glossary", x["name_en"].lower()))
    tabs = "".join(f'<a class="tab{" on" if k == kind else ""}" href="{k}.html">{pair(lb)} <span class="muted">{len(REFS[k])}</span></a>'
                   for k, _, lb in REF_KINDS)
    if kind == "skills":
        tagset = sorted({t for x in items for t in x["skill_types"]})
        flt = [(t, (t, t)) for t in tagset]
    elif kind == "runes":
        flt = [("Tenacity", ("Tenacity", "Tenacity")), ("Versatility", ("Versatility", "Versatility")),
               ("Family", ("Семейства", "Families"))]
    else:
        flt = [("wiki", ("С описанием на вики", "With wiki data")), ("game", ("Только из файлов игры", "Game files only"))]
    flt = [("used", ("В билдах", "In builds"))] + flt
    buttons = "".join(f'<button class="rbtn" data-tag="{e(t)}">{pair(lb)}</button>' for t, lb in flt)
    body = f"""
<section class="hero">
  <h1>{bi("Справочник", "Reference")}</h1>
  <p class="lead">{bi("Данные вики (описания на английском) и названия из файлов игры. «В билдах» — у каких персонажей это встречается в карточках.",
                       "Wiki data (descriptions in English) and names from the game files. 'In builds' lists the characters whose cards use it.")}</p>
  <nav class="tabs rtabs">{tabs}</nav>
  <div class="filters">
    <input id="rq" type="search" placeholder="Поиск / Search" aria-label="Поиск">
    <button class="rbtn on" data-tag="">{bi("Все", "All")}</button>{buttons}
  </div>
  <p class="muted rcount" id="rcount"></p>
</section>
<section class="rlist" id="rgrid">{"".join(ref_item(kind, prefix, x) for x in items)}</section>
<p class="empty" id="empty" hidden>{bi("Ничего не найдено", "Nothing found")}</p>"""
    return page(f"{label[0]} — справочник Soulstone Survivors", body, 1, f"Справочник: {label[1]}")


# ---------- общий гайд ----------
def gtext(t):
    """Текст общего гайда: @Персонаж превращается в ссылку на карточку."""
    import re as _re

    def one(s):
        out, last = [], 0
        for m in _re.finditer(r"@([A-Z][A-Za-z]+)", s):
            out.append(e(s[last:m.start()]))
            out.append(char_link(m.group(1), ""))
            last = m.end()
        out.append(e(s[last:]))
        return "".join(out)
    ru, en = one(t.get("ru", "")), one(t.get("en") or t.get("ru", ""))
    return f'<span class="ru">{ru}</span><span class="en">{en}</span>' if ru != en else ru


def build_general():
    global UP
    UP = ""
    data = json.loads((ROOT / "data" / "common" / "general.json").read_text(encoding="utf-8"))
    src = data["source"]
    secs, toc = [], []
    for sec in data["sections"]:
        toc.append(f'<li><a href="#{sec["id"]}">{txt(sec["title"])}</a></li>')
        html_ = f'<section class="block" id="{sec["id"]}"><h2>{txt(sec["title"])}</h2>'
        for para in sec.get("paras", []):
            html_ += f"<p>{gtext(para)}</p>"
        if sec.get("table"):
            head = "".join(f"<th>{txt(h)}</th>" for h in sec["table"]["head"])
            rows = "".join("<tr>" + "".join(f"<td>{gtext(c)}</td>" for c in r) + "</tr>" for r in sec["table"]["rows"])
            html_ += f'<div class="tablewrap"><table class="gtable"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
        if sec.get("list"):
            html_ += "<ol class=\"rules\">" + "".join(f"<li>{gtext(li)}</li>" for li in sec["list"]) + "</ol>"
        if sec.get("checks"):
            checks = [dict(x, verified_by="wiki") if x["status"] == "verified" else x for x in sec["checks"]]
            html_ += claims_block(checks).replace(bi("Утверждения гайда", "Guide claims"), bi("Проверка по вики", "Wiki check"))
        secs.append(html_ + "</section>")
    body = f"""
<section class="hero">
  <h1>{bi("Общий гайд", "General guide")}</h1>
  {txt(data["intro"], "p", "lead")}
  <p class="src"><a href="{e(src['url'])}" rel="noopener">{e(src['title'])}</a> · {e(src['author'])} ·
     {bi("обновлён", "updated")} {e(src['updated'])} · {bi("пересказ, не копия", "paraphrase, not a copy")}</p>
</section>
<nav class="block toc"><ol>{"".join(toc)}</ol></nav>
{"".join(secs)}"""
    return page("Общий гайд — Soulstone Survivors", body, 0, "Общие правила сборки билдов в Soulstone Survivors")


def main():
    cards = load_cards()
    collect_usage(cards)
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "c").mkdir(parents=True)
    shutil.copytree(ASSETS, DIST / "assets")
    (DIST / "index.html").write_text(build_index(cards), encoding="utf-8")
    for c in REFS["characters"].values():
        (DIST / "c" / f"{c['id']}.html").write_text(build_character(c, cards.get(c["id"])), encoding="utf-8")
    (DIST / "ref").mkdir()
    for kind, prefix, label in REF_KINDS:
        (DIST / "ref" / f"{kind}.html").write_text(build_ref(kind, prefix, label), encoding="utf-8")
    (DIST / "general.html").write_text(build_general(), encoding="utf-8")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    print(f"dist/: главная + {len(REFS['characters'])} персонажей, из них с карточкой {len(cards)}")


if __name__ == "__main__":
    main()
