"""Справочник: raw/wiki + глоссарий -> data/reference/*.json. Без ИИ, только stdlib.

Запуск: python scripts/build_reference.py
Источники: Lua-модули Skills/Runes/Powers Data, страницы персонажей (Infobox, weapon card,
achievements), таблицы пассивок на странице Powers, ../soulstone-guides/glossary.md (RU).
id = английское название без всего, кроме латиницы и цифр (RainofArrows, BloodgodsLegacy).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# raw/ не хранится в git: на GitHub для сборки сайта выкачка не нужна, поэтому её отсутствие не ошибка
_WIKI_DAYS = sorted((ROOT / "raw" / "wiki").glob("*"))
WIKI = _WIKI_DAYS[-1] if _WIKI_DAYS else ROOT / "raw" / "wiki" / "missing"
# копия глоссария лежит в проекте (data/glossary.md); исходник — ../soulstone-guides/glossary.md
GLOSSARY = ROOT / "data" / "glossary.md"
OUT = ROOT / "data" / "reference"
WIKI_URL = "https://soulstone-survivors.fandom.com/wiki/"


def rid(name):
    return re.sub(r"[^A-Za-z0-9]", "", name)


def read(title):
    return (WIKI / (title.replace("/", "_").replace(":", "_") + ".wikitext")).read_text(encoding="utf-8")


# ---------- Lua-таблицы ----------
def parse_lua_table(src):
    """Разбирает первую таблицу-конструктор Lua ({...}) из текста модуля."""
    src = re.sub(r"--\[\[.*?\]\]", "", src, flags=re.S)
    src = re.sub(r"--[^\n]*", "", src)
    toks = re.findall(r'"(?:\\.|[^"\\])*"|-?\d+(?:\.\d+)?|[A-Za-z_]\w*|[{}=,\[\]]', src)
    pos = [toks.index("{")]

    def value():
        t = toks[pos[0]]
        if t == "{":
            return table()
        pos[0] += 1
        if t.startswith('"'):
            return json.loads(t)
        if re.fullmatch(r"-?\d+(?:\.\d+)?", t):
            return float(t) if "." in t else int(t)
        return {"true": True, "false": False, "nil": None}.get(t, t)

    def table():
        pos[0] += 1  # {
        named, items = {}, []
        while toks[pos[0]] != "}":
            if toks[pos[0]] == ",":
                pos[0] += 1
                continue
            if toks[pos[0]] == "[":
                key = json.loads(toks[pos[0] + 1]) if toks[pos[0] + 1].startswith('"') else toks[pos[0] + 1]
                pos[0] += 4  # [ key ] =
                named[key] = value()
            elif pos[0] + 1 < len(toks) and toks[pos[0] + 1] == "=" and re.match(r"[A-Za-z_]", toks[pos[0]]):
                key = toks[pos[0]]
                pos[0] += 2
                named[key] = value()
            else:
                items.append(value())
        pos[0] += 1
        return named if named or not items else items

    return value()


# ---------- викитекст -> простой текст ----------
VALUE_TPL = {"r1", "r2", "r3", "r4", "r5", "rt", "yellow", "blue", "green", "red", "bg color"}
FIRST_ARG_TPL = {"cl", "wp", "as", "ac", "rune", "st", "ap"}


def plain(s):
    if not s:
        return ""
    s = s.replace("{{!}}", "\x00")
    for _ in range(8):
        def tpl(m):
            parts = [p.strip() for p in m.group(1).split("|")]
            name, args = parts[0], parts[1:]
            low = name.lower().lstrip("#")
            if low in VALUE_TPL and args:
                return args[-1]
            if low in ("sc", "sca") and len(args) >= 2:
                return f"{args[0]} {args[1]}"
            if low == "rune" and len(args) >= 2:
                return f"{args[0]}: {args[1]}"
            if low in FIRST_ARG_TPL and args:
                return args[0]
            if low in ("minor soulstones", "rogue soulstones", "green soulstones") and args:
                return f"{args[0]} {name}"
            return name if not args else args[-1] if low.startswith("invoke") else name
        n = re.sub(r"\{\{([^{}]*)\}\}", tpl, s)
        if n == s:
            break
        s = n
    s = re.sub(r"\[\[File:[^\]]*\]\]", "", s)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"<br\s*/?>", "; ", s)
    s = re.sub(r"<[^>]+>|'{2,}", "", s)
    return re.sub(r"\s+", " ", s.replace("\x00", "|")).strip()


def stat_list(s):
    return [{"name": plain(a), "value": b.strip()} for a, b in re.findall(r"\{\{sca?\|([^|{}]+)\|([^{}]*)\}\}", s or "")]


def skill_ids(s):
    return [rid(x) for x in re.findall(r"\{\{as\|([^|}]+)", s or "")]


# ---------- глоссарий ----------
def load_glossary():
    gl, sec = {}, None
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            sec = line[3:].strip()
            gl[sec] = {}
        elif sec and line.startswith("|") and not line.startswith("|--") and "Русское" not in line:
            ru, en = [c.strip() for c in line.strip("|").split("|", 1)]
            for variant in en.split(" / "):
                gl[sec].setdefault(variant.strip(), ru)
    return gl


def ru_lookup(gl, name_en, prefer):
    for sec in prefer:
        if name_en in gl.get(sec, {}):
            return gl[sec][name_en]
    for sec in gl:
        if name_en in gl[sec]:
            return gl[sec][name_en]
    key = rid(name_en).lower()  # Blood Shed (вики) = Bloodshed (игра)
    for sec in prefer + list(gl):
        for en, ru in gl.get(sec, {}).items():
            if rid(en).lower() == key:
                return ru
    return None


# ---------- Lua-модули ----------
def build_skills(gl):
    data = parse_lua_table(read("Module:Skills/Data"))
    out = []
    for key, v in data.items():
        name = v.get("Name", key)
        out.append({
            "id": key, "name_en": name, "name_ru": ru_lookup(gl, name, ["Активные навыки"]),
            "description": plain(v.get("Description")),
            "skill_types": v.get("SkillTypes", []),
            "stats": v.get("Stats", {}).get("DisplayStats", []),
            "unlock": plain(v.get("UnlockConditions")),
            "tags": {k: x for k, x in (v.get("Tags") or {}).items() if x and k != "Scaling"},
            "wiki_url": WIKI_URL + name.replace(" ", "_"),
        })
    return out


def build_runes(gl, char_pages):
    data = parse_lua_table(read("Module:Runes/Data"))
    out = []
    for key, v in data.items():
        name = v.get("Name", key)
        out.append({
            "id": key, "name_en": name, "name_ru": ru_lookup(gl, name, ["Руны"]),
            "section": v.get("Section"), "description": plain(v.get("Description")),
            "runic_power_cost": v.get("RunicPowerCost"), "skill_tree": plain(v.get("SkillTree")),
            "unlock_cost": plain(v.get("UnlockCost")), "rarity": v.get("Rarity"),
            "category": v.get("Category"), "family": False,
            "wiki_url": WIKI_URL + "Runes",
        })
    # руны-семейства: {{rune|Skill Mastery|Projectile}} в достижениях персонажей
    fam = {}
    for ch, text in char_pages.items():
        for m in re.finditer(r"\*\{\{ac\|[^|]*\|rune\|(.*)\}\}\s*$", text, re.M):
            row = m.group(1)
            r = re.search(r"\{\{rune\|([^|}]+)\|([^|}]+)\}\}", row)
            if not r:
                continue
            f = fam.setdefault(r.group(1).strip(), {})
            f[r.group(2).strip()] = {"character": ch, "unlock": plain(row.split("Unlocks")[0])}
    for name, variants in sorted(fam.items()):
        out.append({"id": rid(name), "name_en": name, "name_ru": ru_lookup(gl, name, ["Руны"]),
                    "family": True, "variants": variants, "wiki_url": WIKI_URL + "Runes"})
    return out


def build_powers(gl):
    out = {}
    for key, v in parse_lua_table(read("Module:Powers/Data")).items():
        out[key] = {"id": key, "name_en": v.get("Name", key), "description": plain(v.get("Description")),
                    "note": plain(v.get("Note")), "rarities": list((v.get("Rarities") or {}).keys()),
                    "stats": [], "source": "module"}
    # таблицы на странице Powers: иконка, имя, описание, стат + 5 редкостей; строки без иконки — доп. стат.
    # Ячейка с colspan="5" — одно значение на все редкости, раскрываем её в 5 одинаковых.
    rar = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
    text = read("Powers")
    text = re.sub(r"\[\[File:[^\]]*\]\]", "", text)
    cur = None
    for chunk in re.split(r"\n\|-[^\n]*\n", text):
        if "{|" in chunk or "|}" in chunk or "\n=" in chunk:
            cur = None  # новая таблица или раздел: строки-продолжения не должны тянуться дальше
        cells = []
        for line in chunk.split("\n"):
            if not line.startswith("|") or line.startswith(("|}", "|+", "|-")):
                continue
            body = line[1:]
            m = re.match(r'\s*((?:\w[\w-]*="[^"]*"\s*)+)\|(?!\|)(.*)$', body)
            attrs, content = (m.group(1), m.group(2)) if m else ("", body)
            span = re.search(r'colspan="(\d+)"', attrs)
            cells += [plain(content)] * (int(span.group(1)) if span else 1)
        if len(cells) == 9:
            name = cells[1]
            if not name:
                cur = None
                continue
            cur = out.setdefault(rid(name), {"id": rid(name), "name_en": name, "rarities": [], "stats": [],
                                              "source": "table"})
            cur.setdefault("description", cells[2])
            cur["stats"].append({"name": cells[3], "values": dict(zip(rar, cells[4:]))})
        elif len(cells) == 6 and cur is not None:
            cur["stats"].append({"name": cells[0], "values": dict(zip(rar, cells[1:]))})
        else:
            cur = None
    # страницы статусов (Bleed, Poison...): {{row power|иконка|имя|редкость|описание|статы}}
    for f in sorted(WIKI.glob("*.wikitext")):
        for tpl in block(f.read_text(encoding="utf-8"), r"\{\{row power\|"):
            parts = split_top(tpl[2:-2])
            if len(parts) < 5:
                continue
            name = plain(parts[2])
            p = out.setdefault(rid(name), {"id": rid(name), "name_en": name, "rarities": [], "stats": [],
                                           "source": "row power"})
            p.setdefault("description", plain(parts[4]))
            rarity = parts[3].strip().capitalize()
            if rarity and rarity not in p["rarities"]:
                p["rarities"].append(rarity)
            if len(parts) > 5 and not p["stats"]:
                p["stats"] = [{"name": s["name"], "values": {rarity: s["value"]}} for s in stat_list(parts[5])]
            p.setdefault("pages", [])
            if f.stem not in p["pages"]:
                p["pages"].append(f.stem)
    # семейство Skill Chain: «тип -> тип», шанс цепочки по редкостям (страница Skill Chain)
    out["SkillChain"] = {"id": "SkillChain", "name_en": "Skill Chain", "family": True,
                         "variant_format": "<Skill Type> -> <Skill Type>",
                         "description": "Chance for a skill of one type to automatically cast a skill of another type.",
                         "rarities": ["Rare", "Epic", "Legendary"], "source": "page Skill Chain",
                         "stats": [{"name": "Chain Chance", "values": {"Rare": "+6%", "Epic": "+8%", "Legendary": "+10%"}}]}
    # названия пассивок из файлов игры (глоссарий): только имя, без чисел. Вики знает не все пассивки.
    known = {k.lower() for k in out}
    for en, ru in gl.get("Пассивные бонусы и силы", {}).items():
        if rid(en).lower() not in known:
            out[rid(en)] = {"id": rid(en), "name_en": en, "rarities": [], "stats": [], "source": "game-glossary"}
            known.add(rid(en).lower())
    for p in out.values():
        if not p["rarities"]:
            p["rarities"] = [r for r in rar if any(s.get("values", {}).get(r) for s in p["stats"])]
        p["name_ru"] = ru_lookup(gl, p["name_en"], ["Пассивные бонусы и силы"])
        p["wiki_url"] = WIKI_URL + "Powers"
    return list(out.values())


def split_top(s):
    """Делит по | только на верхнем уровне (не внутри {{...}} и [[...]])."""
    parts, depth, cur, i = [], 0, "", 0
    while i < len(s):
        two = s[i:i + 2]
        if two in ("{{", "[["):
            depth += 1
            cur += two
            i += 2
        elif two in ("}}", "]]"):
            depth -= 1
            cur += two
            i += 2
        elif s[i] == "|" and depth == 0:
            parts.append(cur)
            cur = ""
            i += 1
        else:
            cur += s[i]
            i += 1
    parts.append(cur)
    return parts


# ---------- персонажи и оружие ----------
def block(text, start_pat):
    """Возвращает тела блоков {{...}} (с учётом вложенности), начинающихся с start_pat."""
    res = []
    for m in re.finditer(start_pat, text):
        depth, i = 0, m.start()
        while i < len(text):
            if text.startswith("{{", i):
                depth += 1
                i += 2
            elif text.startswith("}}", i):
                depth -= 1
                i += 2
                if depth == 0:
                    break
            else:
                i += 1
        res.append(text[m.start():i])
    return res


def fields(body):
    f, key = {}, None
    for line in body.split("\n")[1:]:
        m = re.match(r"\s*\|\s*([\w-]+)\s*=\s*(.*)$", line)
        if m:
            key = m.group(1)
            f[key] = m.group(2)
        elif key and line.strip() not in ("}}", ""):
            f[key] += "\n" + line
    return f


def build_characters(gl):
    chars, weapons, pages = [], [], {}
    for f in sorted(WIKI.glob("The *.wikitext")):
        title = f.stem
        name = title[4:]
        text = f.read_text(encoding="utf-8")
        pages[name] = text
        infobox = block(text, r"\{\{Infobox character")
        if not infobox:
            continue  # страница вроде The Void King или The Scorching Valley, не персонаж
        info = fields(infobox[0])
        w_ids = []
        for card in block(text, r"\{\{weapon card"):
            wf = fields(card)
            wname = plain(wf.get("name", "")).strip()
            wid = rid(wname)
            w_ids.append(wid)
            weapons.append({
                "id": wid, "name_en": wname, "name_ru": ru_lookup(gl, wname, ["Оружие"]),
                "character_id": rid(name), "rarity": (wf.get("rarity") or "").strip(),
                "skill_type": plain(wf.get("type", "")), "stats": stat_list(wf.get("stats")),
                "skills": skill_ids(wf.get("skills")), "artifact_power": plain(wf.get("ap", "")),
                "artifact_power_description": plain(wf.get("ap-description", "")),
                "artifact_power_stats": stat_list(wf.get("ap-stats")),
                "wiki_url": WIKI_URL + title.replace(" ", "_"),
            })
        skill_list = ""
        m = re.search(r"==Skill List==(.*?)(?:\n==[^=]|\Z)", text, re.S)
        if m:
            skill_list = m.group(1)
        runes_tree = [plain(x) for x in re.findall(r"\|name=([^\n]+)\n\s*\|rune=(?:true|build)", text)]
        chars.append({
            "id": rid(name), "name_en": name, "name_ru": ru_lookup(gl, name, ["Персонажи"]),
            "class": plain(info.get("class", "")), "weapon_type": plain(info.get("weapon-type", "")),
            "unlock": plain(info.get("unlock", "")), "stats": stat_list(info.get("stats")),
            "skill_types": [plain(x) for x in re.findall(r"\{\{([^{}|]+)\}\}", info.get("skill-types", ""))],
            "weapons": w_ids, "artifact_power": plain(info.get("artifact-power", "")),
            "starting_unique_skills": [plain(info[k]) for k in sorted(info) if k.startswith("us-")],
            "skill_list": skill_ids(skill_list), "tree_runes": runes_tree,
            "has_ascension": "no-ascended" not in info,
            "wiki_url": WIKI_URL + title.replace(" ", "_"),
        })
    return chars, weapons, pages


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    gl = load_glossary()
    chars, weapons, pages = build_characters(gl)
    skills = build_skills(gl)
    runes = build_runes(gl, pages)
    powers = build_powers(gl)
    for name, data in [("characters", chars), ("weapons", weapons), ("skills", skills),
                       ("runes", runes), ("powers", powers)]:
        (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        ru = sum(1 for x in data if x.get("name_ru"))
        print(f"{name:11} {len(data):4} записей, русское имя у {ru}")


if __name__ == "__main__":
    main()
