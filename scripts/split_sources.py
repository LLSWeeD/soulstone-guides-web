"""Нарезка источников по персонажам для шага Extract: work/<Id>/{meta.md, cubic_builds.md, steam.md}.

Запуск: python scripts/split_sources.py [Id ...]   (без аргументов: все персонажи без готовой карточки)
Агент читает только эти три файла (+ схему и lookup.py), а не целые гайды.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "data" / "reference"
CLEAN = ROOT / "clean"
OUT = ROOT / "work"


def load(name):
    return json.loads((REF / f"{name}.json").read_text(encoding="utf-8"))


def steam_sections():
    text = (CLEAN / "pages" / "steam-3251066730.md").read_text(encoding="utf-8")
    body = text.split("---", 2)[-1]
    marks = [(m.start(), m.group(1)) for m in re.finditer(r"^The ([A-Z][A-Za-z ]+)$", body, re.M)]
    end_marker = body.find("Q&A / Update Notes")
    out = {}
    for i, (start, name) in enumerate(marks):
        stop = marks[i + 1][0] if i + 1 < len(marks) else (end_marker if end_marker > start else len(body))
        sec = body[start:stop]
        sec = re.sub(r"\n_{5,}\n", "\n", sec)
        sec = re.sub(r"\n{3,}", "\n\n", sec).strip() + "\n"
        out[re.sub(r"\s+", "", name)] = sec
    return out


def cubic_files():
    res = {}
    for f in (CLEAN / "cubiccreativity").glob("*.md"):
        m = re.search(r"The ([A-Za-z ]+)\.md$", f.name)
        if m:
            res[re.sub(r"\s+", "", m.group(1))] = f
    return res


def main():
    chars = {c["id"]: c for c in load("characters")}
    weapons = load("weapons")
    steam, cubic = steam_sections(), cubic_files()
    ids = sys.argv[1:] or [c for c in chars if not (ROOT / "data" / "characters" / f"{c}.json").exists()]
    for cid in ids:
        c = chars[cid]
        d = OUT / cid
        d.mkdir(parents=True, exist_ok=True)
        ws = [w for w in weapons if w["character_id"] == cid]
        lines = [f"# {cid} ({c['name_en']}, RU: {c.get('name_ru')})", "",
                 f"- Класс: {c['class']}; тип оружия: {c['weapon_type']}; открытие: {c['unlock']}",
                 f"- Типы навыков: {', '.join(c['skill_types'])}",
                 f"- Бонусы: {', '.join(s['name'] + ' ' + s['value'] for s in c['stats'])}",
                 f"- Уникальные навыки: {', '.join(c['starting_unique_skills'])}",
                 f"- Руны дерева: {', '.join(c['tree_runes'])}", "", "## Оружие (id, редкость, навыки)"]
        for w in sorted(ws, key=lambda x: x["rarity"]):
            lines.append(f"- {w['id']} | {w['name_en']} | {w['rarity']} | {w['skill_type']} | навыки: {', '.join(w['skills'])}")
        if not any(w["rarity"] == "R5" for w in ws) and cid != "Blacksmith":
            lines.append("- (легендарного R5 на вики нет)")
        lines += ["", "## Источники"]
        if cid in cubic:
            raw = cubic[cid].read_text(encoding="utf-8")
            head = dict(re.findall(r"^(source|title|published|modified|fetched): (.*)$", raw, re.M))
            upd = re.search(r"\*\*Last updated: ([^*]+)\*\*", raw)
            builds = re.split(r"## (?:\*\*)?Example Builds", raw, maxsplit=1)  # у Spellblade заголовок слеплен с первым билдом
            lines.append(f"- cubiccreativity: {head.get('title')} | {head.get('source')} | {upd.group(1) if upd else 'нет строки Last updated'}")
            body = "## Example Builds\n\n" + builds[1] if len(builds) > 1 else "(раздел Example Builds не найден)"
            (d / "cubic_builds.md").write_text(body, encoding="utf-8")
        else:
            lines.append("- cubiccreativity: гайда нет")
            (d / "cubic_builds.md").unlink(missing_ok=True)
        if cid in steam:
            lines.append("- Steam 3251066730: https://steamcommunity.com/sharedfiles/filedetails/?id=3251066730 | "
                         "«Unique and Detailed Character Builds (All Characters)» | версия 1.2 | обновлён 2025-08-20 | fetched 2026-10-06")
            (d / "steam.md").write_text(steam[cid], encoding="utf-8")
        else:
            lines.append("- Steam: раздела нет")
            (d / "steam.md").unlink(missing_ok=True)
        (d / "meta.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        sizes = {p.name: p.stat().st_size // 1000 for p in d.iterdir()}
        print(f"{cid:14} {sizes}")


if __name__ == "__main__":
    main()
