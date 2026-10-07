"""Данные вики по id или странице (для шага сверки): описание, статы, типы, источник.

Запуск:
  python scripts/describe.py runes Synchrony ElementalFlow
  python scripts/describe.py skills Bladestorm
  python scripts/describe.py powers Magnetic SkillChain
  python scripts/describe.py weapons NoxiousLongbow
  python scripts/describe.py characters Sentinel
  python scripts/describe.py page Aptitude Bleed        (начало статьи вики простым текстом)
Ничего не меняет, только печатает.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_reference import WIKI, plain  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "data" / "reference"


def fmt_stats(stats):
    out = []
    for s in stats or []:
        if "values" in s:
            vals = ", ".join(f"{k}: {v}" for k, v in s["values"].items() if v)
            out.append(f"{s['name']} [{vals}]")
        else:
            out.append(f"{s.get('name', s.get('Name'))} {s.get('value', s.get('Value'))}")
    return "; ".join(out)


def show(kind, x):
    lines = [f"== {kind}:{x['id']} | {x.get('name_en')} | RU: {x.get('name_ru') or '-'}"]
    for key in ("section", "rarity", "runic_power_cost", "skill_tree", "class", "weapon_type",
                "character_id", "skill_type", "source", "unlock", "unlock_cost", "category"):
        if x.get(key) not in (None, "", []):
            lines.append(f"   {key}: {x[key]}")
    if x.get("skill_types"):
        lines.append(f"   types: {', '.join(x['skill_types'])}")
    if x.get("description"):
        lines.append(f"   desc: {x['description']}")
    if x.get("note"):
        lines.append(f"   note: {x['note']}")
    if x.get("stats"):
        lines.append(f"   stats: {fmt_stats(x['stats'])}")
    if x.get("skills"):
        lines.append(f"   skills: {', '.join(x['skills'])}")
    if x.get("artifact_power"):
        lines.append(f"   artifact power: {x['artifact_power']} — {x.get('artifact_power_description', '')}")
    if x.get("family"):
        v = x.get("variants")
        lines.append(f"   family: {', '.join(v) if isinstance(v, dict) else x.get('variant_format', '')}")
    if x.get("weapons"):
        lines.append(f"   weapons: {', '.join(x['weapons'])}")
    if x.get("source") == "game-glossary":
        lines.append("   (есть в файлах игры, на вики нет описания и чисел)")
    print("\n".join(lines))


def page(title):
    f = WIKI / (title.replace("/", "_").replace(":", "_") + ".wikitext")
    if not f.exists():
        print(f"== page:{title} — нет такой страницы в выкачке")
        return
    t = f.read_text(encoding="utf-8")
    t = re.sub(r"\{\{Infobox.*?\n\}\}", "", t, flags=re.S)
    t = plain(t)
    print(f"== page:{title}\n   {t[:1500]}")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    kind, ids = sys.argv[1], sys.argv[2:]
    if kind == "page":
        for t in ids:
            page(t)
        return
    data = {x["id"]: x for x in json.loads((REF / f"{kind}.json").read_text(encoding="utf-8"))}
    for i in ids:
        if i in data:
            show(kind, data[i])
        else:
            print(f"== {kind}:{i} — нет в справочнике (используй lookup.py для поиска по названию)")


if __name__ == "__main__":
    main()
