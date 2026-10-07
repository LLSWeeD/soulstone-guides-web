"""Поиск id в справочнике по названию (для исполнителей шага Extract).

Запуск: python scripts/lookup.py <skills|runes|powers|weapons|characters> "Название 1" "Название 2" ...
Для рун-семейств и Skill Chain понимает форму «Семейство: Вариант»:
  python scripts/lookup.py runes "Skill Mastery: Projectile"
  python scripts/lookup.py powers "Skill Chain: Earth -> Thrust"
Выводит id (и variant), либо NOT FOUND с ближайшими названиями. Ничего не выдумывает.
"""
import json
import re
import sys
from difflib import get_close_matches
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "data" / "reference"


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("skills", "runes", "powers", "weapons", "characters"):
        print(__doc__)
        return
    kind, queries = sys.argv[1], sys.argv[2:]
    items = json.loads((REF / f"{kind}.json").read_text(encoding="utf-8"))
    by_norm = {}
    for x in items:
        by_norm.setdefault(norm(x["name_en"]), x)
        by_norm.setdefault(norm(x["id"]), x)
    skill_types = None
    for q in queries:
        base, variant = q, None
        if ":" in q:
            b, v = [p.strip() for p in q.split(":", 1)]
            fam = by_norm.get(norm(b))
            if fam and fam.get("family"):
                base, variant = b, v
        hit = by_norm.get(norm(base))
        if hit:
            line = f'{q!r:40} -> {hit["id"]}'
            if hit.get("family"):
                if kind == "runes":
                    ok = variant in hit.get("variants", {})
                    line += f'  variant={variant!r}' + ("" if ok else f'  !! варианта нет, есть: {", ".join(hit["variants"])}')
                else:
                    if skill_types is None:
                        skill_types = {t for s in json.loads((REF / "skills.json").read_text(encoding="utf-8"))
                                       for t in s["skill_types"]}
                    m = re.fullmatch(r"\s*(\w+)\s*->\s*(\w+)\s*", variant or "")
                    ok = bool(m) and {m.group(1), m.group(2)} <= skill_types
                    line += f'  variant={variant!r}' + ("" if ok else "  !! нужен вариант «Тип -> Тип» (типы навыков)")
            extra = hit.get("section") or hit.get("rarity") or hit.get("source") or ""
            print(line + (f'   [{extra}]' if extra else "") + (f'  ({hit["name_ru"]})' if hit.get("name_ru") else ""))
        else:
            names = {x["name_en"]: x for x in items}
            close = get_close_matches(base, list(names), n=3, cutoff=0.6)
            print(f'{q!r:40} -> NOT FOUND' + (f'  ближайшие: {", ".join(f"{c} ({names[c]["id"]})" for c in close)}' if close else ""))


if __name__ == "__main__":
    main()
