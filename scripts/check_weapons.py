"""Проверка weapon_id в карточках: оружие должно быть названо в тексте гайда этого билда.

Запуск: python scripts/check_weapons.py [--fix] [Id ...]
Без --fix только печатает расхождения. С --fix у билдов, где оружие в гайде не названо, ставит
weapon_id = null и добавляет в gaps строку «оружие не названо, по навыкам вероятно X».
Нужны входные файлы work/<Id>/ (scripts/split_sources.py).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "data" / "characters"
WORK = ROOT / "work"
WEAPONS = {w["id"]: w for w in json.loads((ROOT / "data" / "reference" / "weapons.json").read_text(encoding="utf-8"))}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fix = "--fix" in sys.argv
    ids = args or [p.stem for p in sorted(CARDS.glob("*.json"))]
    total = 0
    for cid in ids:
        path = CARDS / f"{cid}.json"
        card = json.loads(path.read_text(encoding="utf-8"))
        texts = {}
        for g in card["guides"]:
            f = WORK / cid / ("steam.md" if g["source_id"].startswith("steam") else "cubic_builds.md")
            texts[g["source_id"]] = norm(f.read_text(encoding="utf-8")) if f.exists() else ""
        changed = False
        for g in card["guides"]:
            for b in g["builds"]:
                wid = b.get("weapon_id")
                if not wid:
                    continue
                name = WEAPONS[wid]["name_en"]
                if norm(name) in texts[g["source_id"]]:
                    continue
                total += 1
                bs = {s["id"] for s in b["skills"]}
                hit = len(set(WEAPONS[wid]["skills"]) & bs)
                print(f'{cid:13} {b["id"]:34} оружие {name!r} в гайде не названо (его навыков в билде: {hit}/{len(WEAPONS[wid]["skills"])})')
                if fix:
                    b["weapon_id"] = None
                    card["gaps"].append(f'Оружие билда «{b["name"]["ru"]}» гайд не называет; по навыкам вероятно {name} '
                                        f'(в карточке не указано как вывод).')
                    changed = True
        if fix and changed:
            path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"всего без названия в гайде: {total}")


if __name__ == "__main__":
    main()
