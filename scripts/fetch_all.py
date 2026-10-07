"""Выкачка сырья в raw/<источник>/<дата>/. Без ИИ, без сторонних зависимостей.

Запуск: python scripts/fetch_all.py [wiki] [cubic] [pages]
Без аргументов качает всё. Повторно ничего не качает, если файл уже есть.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DAY = date.today().isoformat()
UA = "Mozilla/5.0 (personal research; soulstone-guides-web)"
PAUSE = 1.0

WIKI_API = "https://soulstone-survivors.fandom.com/api.php"
CUBIC_API = "https://public-api.wordpress.com/rest/v1.1/sites/cubiccreativity.wordpress.com/posts/"

PAGES = {
    "lb-product": "https://game.lb-product.com/en/games/soulstone-survivors/guides/soulstone-survivors_builds-guide",
    "steam-3251066730": "https://steamcommunity.com/sharedfiles/filedetails/?id=3251066730",
    "steam-3376319812": "https://steamcommunity.com/sharedfiles/filedetails/?id=3376319812",
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def get_json(url):
    return json.loads(get(url).decode("utf-8"))


def safe(name):
    return re.sub(r'[<>:"/\\|?*]', "_", name)


def out_dir(source):
    d = ROOT / "raw" / source / DAY
    d.mkdir(parents=True, exist_ok=True)
    return d


def fetch_wiki():
    d = out_dir("wiki")
    titles = []
    # 0 — статьи, 828 — Lua-модули (в Module:*/Data лежат таблицы навыков, пассивок, рун)
    for ns in ("0", "828"):
        cont = {}
        while True:
            q = {"action": "query", "list": "allpages", "aplimit": "500", "apnamespace": ns,
                 "apfilterredir": "nonredirects", "format": "json", **cont}
            data = get_json(WIKI_API + "?" + urllib.parse.urlencode(q))
            titles += [p["title"] for p in data["query"]["allpages"]
                       if ns == "0" or p["title"].endswith("/Data")]
            if "continue" not in data:
                break
            cont = data["continue"]
            time.sleep(PAUSE)
    print(f"wiki: {len(titles)} страниц")
    (d / "_titles.json").write_text(json.dumps(titles, ensure_ascii=False, indent=1), encoding="utf-8")
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        if all((d / (safe(t) + ".wikitext")).exists() for t in batch):
            continue
        q = {"action": "query", "prop": "revisions", "rvprop": "content|timestamp",
             "rvslots": "main", "titles": "|".join(batch), "format": "json"}
        data = get_json(WIKI_API + "?" + urllib.parse.urlencode(q))
        for page in data["query"]["pages"].values():
            rev = page.get("revisions", [{}])[0]
            text = rev.get("slots", {}).get("main", {}).get("*", "")
            (d / (safe(page["title"]) + ".wikitext")).write_text(text, encoding="utf-8")
            (d / (safe(page["title"]) + ".meta.json")).write_text(
                json.dumps({"title": page["title"], "revised": rev.get("timestamp"),
                            "url": "https://soulstone-survivors.fandom.com/wiki/"
                                   + urllib.parse.quote(page["title"].replace(" ", "_"))},
                           ensure_ascii=False), encoding="utf-8")
        print(f"  wiki {min(i + 50, len(titles))}/{len(titles)}")
        time.sleep(PAUSE)


def fetch_cubic():
    d = out_dir("cubiccreativity")
    q = {"search": "soulstone", "number": "100",
         "fields": "ID,title,URL,date,modified,content"}
    data = get_json(CUBIC_API + "?" + urllib.parse.urlencode(q))
    n = 0
    for p in data["posts"]:
        if not p["title"].startswith("Soulstone Survivors Guide"):
            continue
        name = safe(re.sub(r"&#\d+;|&\w+;", "", p["title"]).strip())
        (d / (name + ".json")).write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8")
        n += 1
    print(f"cubiccreativity: {n} гайдов из {data['found']} найденных постов")


def fetch_pages():
    d = out_dir("pages")
    for name, url in PAGES.items():
        f = d / (name + ".html")
        if f.exists():
            continue
        try:
            f.write_bytes(get(url))
            print(f"pages: {name} {f.stat().st_size} байт")
        except Exception as e:  # noqa: BLE001
            print(f"pages: {name} ОШИБКА {e}")
        (d / (name + ".url")).write_text(url, encoding="utf-8")
        time.sleep(PAUSE)


if __name__ == "__main__":
    what = set(sys.argv[1:]) or {"wiki", "cubic", "pages"}
    if "wiki" in what:
        fetch_wiki()
    if "cubic" in what:
        fetch_cubic()
    if "pages" in what:
        fetch_pages()
