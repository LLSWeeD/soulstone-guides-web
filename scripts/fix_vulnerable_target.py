"""Утверждения про руну Vulnerable Target: проверено пользователем в игре (2026-10-08) — +50% шанса крита.

Утверждения с 50% -> verified (verified_by: user), с 25% или без числа -> conflict с пояснением.
Модуль рун на вики старее 1.5d и даёт 25%. Запуск: python scripts/fix_vulnerable_target.py [Id ...]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "data" / "characters"
OK = "Проверено в игре (1.5d): Vulnerable Target даёт +50% шанса крита. На вики устаревшие +25%."
BAD = ("В игре (1.5d) Vulnerable Target даёт +50% шанса крита (проверено пользователем); "
       "25% — старое значение, как на вики. Гайд в этом месте устарел.")


def main():
    ids = sys.argv[1:] or [p.stem for p in sorted(CARDS.glob("*.json"))]
    for cid in ids:
        path = CARDS / f"{cid}.json"
        card = json.loads(path.read_text(encoding="utf-8"))
        n = 0
        for g in card["guides"]:
            for b in g["builds"]:
                for x in b.get("claims", []):
                    if "Vulnerable Target" not in x["text"]["ru"]:
                        continue
                    if re.search(r"50\s*%", x["text"]["ru"]):
                        new = {"status": "verified", "verified_by": "user", "detail": OK}
                    else:
                        new = {"status": "conflict", "verified_by": "user", "detail": BAD}
                    if any(x.get(k) != v for k, v in new.items()):
                        x.update(new)
                        n += 1
        if n:
            path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{cid}: обновлено утверждений {n}")


if __name__ == "__main__":
    main()
