"""Проверка карточек персонажей: схема + сверка названий со справочником.

Запуск: python scripts/validate.py [файл.json ...]   (по умолчанию data/characters/*.json)
Код выхода 1, если есть ошибки (предупреждения его не меняют).
Мини-валидатор схемы без зависимостей: покрывает только то, что есть в нашей схеме
($ref, type, const, enum, pattern, required, properties, additionalProperties:false,
items, minItems, maxItems, anyOf).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "data" / "reference"
SCHEMA = json.loads((ROOT / "schema" / "character-card.schema.json").read_text(encoding="utf-8"))

TYPES = {"string": str, "object": dict, "array": list, "null": type(None),
         "integer": int, "number": (int, float), "boolean": bool}


def resolve(ref):
    node = SCHEMA
    for part in ref.lstrip("#/").split("/"):
        node = node[part]
    return node


def check(inst, sch, path, errs):
    if "$ref" in sch:
        check(inst, resolve(sch["$ref"]), path, errs)
    if "anyOf" in sch:
        trials = []
        for sub in sch["anyOf"]:
            e = []
            check(inst, sub, path, e)
            if not e:
                break
            trials.append(e)
        else:
            errs.append(f"{path}: не подходит ни один вариант ({len(trials)} вар.), первый: {trials[0][0]}")
    if "const" in sch and inst != sch["const"]:
        errs.append(f"{path}: должно быть {sch['const']!r}, а не {inst!r}")
    if "enum" in sch and inst not in sch["enum"]:
        errs.append(f"{path}: {inst!r} не из {sch['enum']}")
    t = sch.get("type")
    if t and not (isinstance(inst, TYPES[t]) and not (t in ("integer", "number") and isinstance(inst, bool))):
        errs.append(f"{path}: ожидался {t}")
        return
    if isinstance(inst, str) and "pattern" in sch and not re.search(sch["pattern"], inst):
        errs.append(f"{path}: {inst!r} не подходит под {sch['pattern']}")
    if isinstance(inst, dict):
        for k in sch.get("required", []):
            if k not in inst:
                errs.append(f"{path}: нет обязательного поля {k}")
        props = sch.get("properties", {})
        for k, v in inst.items():
            if k in props:
                check(v, props[k], f"{path}.{k}", errs)
            elif sch.get("additionalProperties") is False:
                errs.append(f"{path}: лишнее поле {k}")
    if isinstance(inst, list):
        if "minItems" in sch and len(inst) < sch["minItems"]:
            errs.append(f"{path}: минимум {sch['minItems']} элементов")
        if "maxItems" in sch and len(inst) > sch["maxItems"]:
            errs.append(f"{path}: максимум {sch['maxItems']} элементов, есть {len(inst)}")
        if "items" in sch:
            for i, x in enumerate(inst):
                check(x, sch["items"], f"{path}[{i}]", errs)


def load_ref():
    ref = {}
    for name in ("characters", "weapons", "skills", "runes", "powers"):
        ref[name] = {x["id"]: x for x in json.loads((REF / f"{name}.json").read_text(encoding="utf-8"))}
    stats = set()
    for c in ref["characters"].values():
        stats |= {s["name"] for s in c["stats"]}
    for w in ref["weapons"].values():
        stats |= {s["name"] for s in w["stats"]}
    for p in ref["powers"].values():
        stats |= {s["name"].split(" | ")[-1] for s in p["stats"]}
    ref["stat_names"] = stats
    ref["power_names"] = {p["name_en"].lower(): p["id"] for p in ref["powers"].values()}
    ref["skill_types"] = {t for s in ref["skills"].values() for t in s["skill_types"]}
    return ref


def check_refs(card, ref, errs, warns):
    cid = card.get("character_id")
    if cid not in ref["characters"]:
        errs.append(f"character_id {cid!r} нет в справочнике")
        return
    char_weapons = set(ref["characters"][cid]["weapons"])
    seen = set()
    for gi, g in enumerate(card.get("guides", [])):
        for bi, b in enumerate(g.get("builds", [])):
            p = f"guides[{gi}].builds[{bi}]({b.get('id')})"
            if b.get("id") in seen:
                errs.append(f"{p}: повторяется id билда")
            seen.add(b.get("id"))
            w = b.get("weapon_id")
            if w and w not in ref["weapons"]:
                errs.append(f"{p}.weapon_id: {w!r} нет в справочнике")
            elif w and w not in char_weapons:
                errs.append(f"{p}.weapon_id: {w!r} не оружие персонажа {cid}")
            for s in b.get("skills", []):
                if s["id"] not in ref["skills"]:
                    errs.append(f"{p}.skills: {s['id']!r} нет в справочнике навыков")
            for pw in b.get("passives", []):
                if "power_id" in pw and "power_name" in pw:
                    errs.append(f"{p}.passives: power_id и power_name вместе не нужны, оставь power_id")
                pr = ref["powers"].get(pw.get("power_id"))
                if "power_id" in pw and not pr:
                    errs.append(f"{p}.passives: {pw['power_id']!r} нет в справочнике пассивок; если на вики её нет, пиши power_name")
                elif pr and pr.get("family"):
                    m = re.fullmatch(r"\s*(\w+)\s*->\s*(\w+)\s*", pw.get("variant") or "")
                    if not m or not {m.group(1), m.group(2)} <= ref["skill_types"]:
                        errs.append(f"{p}.passives: у {pw['power_id']} нужен variant вида «Тип -> Тип», есть {pw.get('variant')!r}")
                elif pr and pw.get("variant"):
                    errs.append(f"{p}.passives: {pw['power_id']} не семейство, variant не нужен")
                if "power_name" in pw:
                    hit = ref["power_names"].get(pw["power_name"].lower())
                    if hit and ref["powers"][hit].get("family"):
                        warns.append(f"{p}.passives: {pw['power_name']!r}: семейство без названных типов (гайд их не называет), записано как power_name")
                    elif hit:
                        errs.append(f"{p}.passives: {pw['power_name']!r} есть в справочнике, пиши power_id {hit!r}")
                    else:
                        warns.append(f"{p}.passives: {pw['power_name']!r} нет на вики (записано как power_name)")
                if "stat" in pw and pw["stat"] not in ref["stat_names"]:
                    warns.append(f"{p}.passives: стат {pw['stat']!r} не встречается на вики")
            for slot, runes in (b.get("runes") or {}).items():
                for r in runes:
                    rr = ref["runes"].get(r["id"])
                    if not rr:
                        errs.append(f"{p}.runes.{slot}: {r['id']!r} нет в справочнике рун")
                        continue
                    if rr.get("family"):
                        if r.get("variant") not in rr["variants"]:
                            errs.append(f"{p}.runes.{slot}: у семейства {r['id']} нет варианта {r.get('variant')!r}"
                                        f" (есть: {', '.join(rr['variants'])})")
                    elif r.get("variant"):
                        errs.append(f"{p}.runes.{slot}: {r['id']} не семейство, variant не нужен")
                    sec = (rr.get("section") or "").lower()
                    if sec and sec != slot:
                        warns.append(f"{p}.runes.{slot}: {r['id']} на вики в секции {rr['section']}")
            if g.get("kind") == "legacy" and not b.get("legacy_check"):
                warns.append(f"{p}: у legacy-билда нет legacy_check")
    if not card.get("guides"):
        warns.append("нет ни одного гайда (карточка только из вики)")


def validate_file(path, ref):
    errs, warns = [], []
    try:
        card = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"невалидный JSON: {e}"], []
    check(card, SCHEMA, "$", errs)
    if not errs:
        check_refs(card, ref, errs, warns)
    return errs, warns


if __name__ == "__main__":
    files = sys.argv[1:] or sorted(str(p) for p in (ROOT / "data" / "characters").glob("*.json"))
    ref = load_ref()
    bad = 0
    for f in files:
        errs, warns = validate_file(f, ref)
        print(f"{Path(f).name}: {'OK' if not errs else 'ОШИБОК ' + str(len(errs))}, предупреждений {len(warns)}")
        for e in errs:
            print("  ERROR  ", e)
        for w in warns:
            print("  warning", w)
        bad += bool(errs)
    sys.exit(1 if bad else 0)
