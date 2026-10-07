"""Очистка сырья: raw/ -> clean/ (чистый Markdown-подобный текст по заголовкам).

raw/ не изменяется. Запуск: python scripts/clean.py
Зависимости: только стандартная библиотека.
Вики (wikitext) здесь не чистится: это вход для парсера справочника, а не для чтения.
"""
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, CLEAN = ROOT / "raw", ROOT / "clean"

SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form",
             "button", "iframe", "figure", "img", "select", "aside"}
# блоки WordPress, которые не относятся к тексту гайда
SKIP_CLASS = re.compile(r"sharedaddy|jp-relatedposts|wpcnt|reblog|post-likes|wp-block-buttons"
                        r"|comments|addtoany|share|related|newsletter|cookie|advert|ads?\b")
BLOCK = {"p", "div", "section", "article", "ul", "ol", "table", "blockquote", "tr", "br"}
VOID = {"br", "img", "hr", "meta", "link", "input"}


class Cleaner(HTMLParser):
    """Собирает текст из контейнера. root_match(tag, attrs) выбирает корневой элемент."""

    def __init__(self, root_match=None):
        super().__init__(convert_charrefs=True)
        self.root_match = root_match
        self.in_root = root_match is None
        self.root_depth = 0
        self.depth = 0
        self.skip_depth = None
        self.out = []
        self.row = None
        self.href_stack = []

    def _emit(self, s):
        if self.in_root and self.skip_depth is None:
            self.out.append(s)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag not in VOID:
            self.depth += 1
        if not self.in_root:
            if self.root_match and self.root_match(tag, a):
                self.in_root, self.root_depth = True, self.depth
            return
        if self.skip_depth is not None:
            return
        cls = (a.get("class") or "") + " " + (a.get("id") or "")
        if tag in SKIP_TAGS or SKIP_CLASS.search(cls.lower()):
            self.skip_depth = self.depth
            return
        if re.fullmatch(r"h[1-6]", tag):
            self._emit("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "li":
            self._emit("\n- ")
        elif tag == "tr":
            self.row = []
            self._emit("\n")
        elif tag in ("td", "th"):
            self._emit(" | ")
        elif tag in BLOCK:
            self._emit("\n")
        elif tag in ("strong", "b"):
            self._emit("**")

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.in_root and self.skip_depth is None:
            if re.fullmatch(r"h[1-6]", tag):
                self._emit("\n")
            elif tag in ("strong", "b"):
                self._emit("**")
            elif tag in BLOCK:
                self._emit("\n")
        if self.skip_depth is not None and self.depth <= self.skip_depth:
            self.skip_depth = None
        if self.in_root and self.root_match and self.depth <= self.root_depth:
            self.in_root = False
            self.root_match = lambda *_: False
        self.depth -= 1

    def handle_data(self, data):
        self._emit(data)

    def text(self):
        t = "".join(self.out)
        t = t.replace("\xa0", " ")
        t = re.sub(r"\*\*\s*\*\*", "", t)
        t = re.sub(r"[ \t]+", " ", t)
        t = re.sub(r" *\n *", "\n", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
        return t.strip() + "\n"


def convert(html, root_match=None):
    c = Cleaner(root_match)
    c.feed(html)
    return c.text()


def header(meta):
    lines = ["---"] + [f"{k}: {v}" for k, v in meta.items()] + ["---", ""]
    return "\n".join(lines)


def write(path, meta, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header(meta) + text, encoding="utf-8")
    return len(text)


def latest(source):
    days = sorted((RAW / source).glob("*"))
    return days[-1] if days else None


def clean_cubic():
    d = latest("cubiccreativity")
    n = []
    for f in sorted(d.glob("*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        text = convert(p["content"])
        # хвост после гайда (подписи, ссылки на другие посты) часто начинается с этих маркеров
        text = re.split(r"\n(?:Share this:|Like this:|Related\n)", text)[0].rstrip() + "\n"
        title = re.sub(r"&#\d+;|&\w+;", "", p["title"]).strip()
        meta = {"source": p["URL"], "title": title, "published": p["date"][:10],
                "modified": p["modified"][:10], "fetched": d.name}
        n.append((f.stem, write(CLEAN / "cubiccreativity" / (f.stem + ".md"), meta, text)))
    return n


def clean_pages():
    d = latest("pages")
    roots = {
        "lb-product": lambda t, a: t == "article",
        "steam-3251066730": lambda t, a: "guide subSections" in (a.get("class") or ""),
        "steam-3376319812": lambda t, a: "guide subSections" in (a.get("class") or ""),
    }
    n = []
    for name, match in roots.items():
        f = d / (name + ".html")
        if not f.exists():
            continue
        html = f.read_text(encoding="utf-8", errors="ignore")
        text = convert(html, match)
        url = (d / (name + ".url")).read_text(encoding="utf-8")
        meta = {"source": url, "fetched": d.name}
        n.append((name, write(CLEAN / "pages" / (name + ".md"), meta, text)))
    return n


if __name__ == "__main__":
    for label, items in (("cubiccreativity", clean_cubic()), ("pages", clean_pages())):
        print(label)
        for name, size in items:
            print(f"  {name[-40:]:40} {size // 1000:4} КБ  ~{size // 4000} тыс. токенов")
