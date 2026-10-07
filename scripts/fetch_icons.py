"""Иконки с вики: имена файлов из данных -> проверка через MediaWiki API -> уменьшенные копии в site/icons/.

Запуск: python scripts/fetch_icons.py
Результат: site/icons/<тип>/<id>.png и data/reference/icons.json ({тип: {id: "icons/<тип>/<id>.png"}}).
Повторно уже скачанное не качает. Для сущностей без иконки (например, пассивки только из файлов игры)
в манифесте записи нет, сайт покажет заглушку.
Зависимости: только стандартная библиотека.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_reference import WIKI, parse_lua_table, read, rid  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "data" / "reference"
ICONS = ROOT / "site" / "icons"
API = "https://soulstone-survivors.fandom.com/api.php"
UA = "Mozilla/5.0 (personal research; soulstone-guides-web)"
WIDTH = 96  # px: хватает для 48 px на retina
PAUSE = 1.0


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def png(name):
    name = name.strip().replace(" ", "_")
    return name if re.search(r"\.(png|jpg|jpeg|webp|gif)$", name, re.I) else name + ".png"


def candidates():
    """{тип: {id: [имена файлов по убыванию уверенности]}}"""
    c = {"skills": {}, "runes": {}, "powers": {}, "weapons": {}, "characters": {}}
    for key, v in parse_lua_table(read("Module:Skills/Data")).items():
        if v.get("ImageName"):
            c["skills"][key] = [png(v["ImageName"])]
    for key, v in parse_lua_table(read("Module:Runes/Data")).items():
        if v.get("ImageName"):
            c["runes"][key] = [png(v["ImageName"])]
    # семейства Skill Mastery/Inclination/Affinity: на вики файлы вида <Тип><Mastery|Inclination|Affinity>.png
    for r in json.loads((REF / "runes.json").read_text(encoding="utf-8")):
        if r.get("family"):
            suffix = r["name_en"].split()[-1]
            for variant in r["variants"]:
                c["runes"][f'{r["id"]}_{variant}'] = [png(variant + suffix)]
    for key, v in parse_lua_table(read("Module:Powers/Data")).items():
        if v.get("ImageName"):
            c["powers"][key] = [png(v["ImageName"])]
    # таблицы страницы Powers: [[File:X.png|64px]] перед ячейкой с именем
    text = read("Powers")
    for fname, name in re.findall(r"\[\[File:([^|\]]+)\|[^\]]*\]\]\s*\n\|[^\n]*?\|\s*([^\n|]+?)\s*\n", text):
        c["powers"].setdefault(rid(name), [png(fname)])
    # {{row power|иконка|имя|...}} на страницах статусов
    for f in WIKI.glob("*.wikitext"):
        for icon, name in re.findall(r"\{\{row power\|([^|]*)\|([^|]*)\|", f.read_text(encoding="utf-8")):
            c["powers"].setdefault(rid(name), [png(icon)])
    # персонажи: таблица на странице Characters
    ch = read("Characters")
    for fname, name in re.findall(r"\[\[File:([^|\]]+)\|64x64px\]\]\s*\n\s*\|\s*'''\[\[([^\]|]+)", ch):
        c["characters"][rid(re.sub(r"^The ", "", name))] = [png(fname)]
    # оружие: на карточке нет файла, на вики имя файла = название без пробелов и знаков (проверяется по API)
    for w in json.loads((REF / "weapons.json").read_text(encoding="utf-8")):
        n = w["name_en"]
        # апостроф в имени файла сохраняется (Nature’sFury.png), убираются только пробелы
        c["weapons"][w["id"]] = [png(rid(n)), png(re.sub(r"\s+", "", n)), png(n),
                                 png(re.sub(r"[’']", "", n).replace(" ", ""))]
    return c


def lookup(files):
    """Для списка имён файлов возвращает {имя: thumb-url} только для существующих."""
    found = {}
    files = sorted(files)
    for i in range(0, len(files), 50):
        batch = files[i:i + 50]
        q = {"action": "query", "prop": "imageinfo", "iiprop": "url", "iiurlwidth": str(WIDTH),
             "titles": "|".join("File:" + f for f in batch), "format": "json"}
        data = json.loads(get(API + "?" + urllib.parse.urlencode(q)).decode("utf-8"))
        norm = {n["to"]: n["from"] for n in data["query"].get("normalized", [])}
        for page in data["query"]["pages"].values():
            info = page.get("imageinfo")
            if not info:
                continue
            title = page["title"][len("File:"):]
            orig = norm.get(page["title"], page["title"])[len("File:"):]
            url = info[0].get("thumburl") or info[0]["url"]
            found[title] = url
            found[orig] = url
            found[title.replace(" ", "_")] = url
        print(f"  api {min(i + 50, len(files))}/{len(files)}")
        time.sleep(PAUSE)
    return found


def main():
    cand = candidates()
    all_files = {f for kind in cand.values() for fl in kind.values() for f in fl}
    print(f"кандидатов: {sum(len(k) for k in cand.values())} сущностей, {len(all_files)} файлов")
    found = lookup(all_files)
    manifest, missing = {}, {}
    for kind, items in cand.items():
        manifest[kind] = {}
        missing[kind] = []
        for eid, files in items.items():
            hit = next((f for f in files if f in found or f.replace("_", " ") in found), None)
            if not hit:
                missing[kind].append(eid)
                continue
            url = found.get(hit) or found[hit.replace("_", " ")]
            rel = f"icons/{kind}/{eid}.png"
            dest = ROOT / "site" / rel
            if not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    dest.write_bytes(get(url))
                except Exception as err:  # noqa: BLE001
                    print(f"  ОШИБКА {rel}: {err}")
                    missing[kind].append(eid)
                    continue
                time.sleep(0.15)
            manifest[kind][eid] = rel
        print(f"{kind:10} иконок {len(manifest[kind]):3} из {len(items)}; без иконки: {len(missing[kind])}")
    (REF / "icons.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    size = sum(f.stat().st_size for f in ICONS.rglob("*.png"))
    print(f"всего файлов {sum(len(m) for m in manifest.values())}, {size // 1024} КБ")
    (ROOT / "raw").mkdir(exist_ok=True)
    (ROOT / "raw" / "icons-missing.json").write_text(json.dumps(missing, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
