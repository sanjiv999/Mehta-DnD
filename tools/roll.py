#!/usr/bin/env python3
"""Dice roller, table roller and oracle. Every roll is appended to dm/rolls.log.

  roll.py 2d6+3                 roll dice
  roll.py d20 --adv | --dis     advantage / disadvantage
  roll.py 4d6kh3 -n 6           keep-highest, repeat 6 times
  roll.py --table weather       roll on dm/tables/weather.yaml
  roll.py --table hero-seeds -n 3
  roll.py --oracle likely       yes/no oracle (certain|likely|even|unlikely|impossible)
  roll.py --seed 42 ...         reproducible
"""
from __future__ import annotations
import argparse
import random
import re
import sys
from datetime import datetime
from common import TABLES, ROLL_LOG, load_yaml

DICE = re.compile(r"^(\d*)d(\d+)(?:k([hl])(\d+))?([+-]\d+)?$", re.I)
ORACLE = {"certain": 3, "likely": 7, "even": 11, "unlikely": 15, "impossible": 19}


def log(line: str) -> None:
    ROLL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(ROLL_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat(timespec='seconds')}  {line}\n")


def roll_expr(expr: str, rng: random.Random, adv: int = 0) -> tuple[int, str]:
    """Return (total, detail). adv: +1 advantage, -1 disadvantage, 0 normal."""
    m = DICE.match(expr.replace(" ", ""))
    if not m:
        raise SystemExit(f"Bad dice expression: {expr!r} (try 2d6+3, d20, 4d6kh3)")
    n = int(m.group(1) or 1)
    sides = int(m.group(2))
    keep_mode, keep_n = m.group(3), m.group(4)
    mod = int(m.group(5) or 0)
    if adv and (n != 1 or sides != 20):
        raise SystemExit("Advantage/disadvantage only applies to a single d20.")
    if adv:
        a, b = rng.randint(1, 20), rng.randint(1, 20)
        chosen = max(a, b) if adv > 0 else min(a, b)
        tag = "adv" if adv > 0 else "dis"
        detail = f"[{a}, {b}] {tag} -> {chosen}{f' {mod:+d}' if mod else ''}"
        return chosen + mod, detail
    rolls = [rng.randint(1, sides) for _ in range(n)]
    kept = rolls
    if keep_mode:
        k = int(keep_n)
        kept = sorted(rolls, reverse=(keep_mode.lower() == "h"))[:k]
    total = sum(kept) + mod
    detail = f"{rolls}" + (f" keep {kept}" if keep_mode else "") + (f" {mod:+d}" if mod else "")
    return total, detail


def roll_table(name: str, rng: random.Random):
    path = TABLES / f"{name}.yaml"
    if not path.exists():
        names = ", ".join(p.stem for p in sorted(TABLES.glob("*.yaml")))
        raise SystemExit(f"No table {name!r}. Available: {names}")
    t = load_yaml(path)
    entries, weights = [], []
    for e in t.get("entries", []):
        if isinstance(e, dict):
            entries.append(e.get("text", "")); weights.append(float(e.get("weight", 1)))
        else:
            entries.append(str(e)); weights.append(1.0)
    return rng.choices(entries, weights=weights, k=1)[0]


def oracle(likelihood: str, rng: random.Random) -> str:
    key = likelihood.lower()
    if key not in ORACLE:
        raise SystemExit(f"Likelihood must be one of {', '.join(ORACLE)}")
    thr = ORACLE[key]
    r = rng.randint(1, 20)
    if r == 20:
        answer = "YES, and something better"
    elif r == 1:
        answer = "NO, and something worse"
    elif r >= thr:
        answer = "Yes, but" if r - thr < 2 else "Yes"
    else:
        answer = "No, but" if thr - r <= 2 else "No"
    twist = ""
    if r in (1, 20):
        twist = "  twist: " + roll_table("twists", rng)
    return f"d20={r} (needs {thr}+) -> {answer}{twist}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("expr", nargs="?", help="dice expression, e.g. 2d6+3")
    ap.add_argument("--adv", action="store_true")
    ap.add_argument("--dis", action="store_true")
    ap.add_argument("-n", "--times", type=int, default=1)
    ap.add_argument("--table")
    ap.add_argument("--oracle", metavar="LIKELIHOOD")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--label", default="")
    ap.add_argument("--no-log", action="store_true")
    a = ap.parse_args(argv)
    rng = random.Random(a.seed) if a.seed is not None else random.Random()
    lbl = f" [{a.label}]" if a.label else ""
    lines = []
    for _ in range(a.times):
        if a.table:
            lines.append(f"table:{a.table}{lbl} -> {roll_table(a.table, rng)}")
        elif a.oracle:
            lines.append(f"oracle:{a.oracle}{lbl} -> {oracle(a.oracle, rng)}")
        elif a.expr:
            total, detail = roll_expr(a.expr, rng, 1 if a.adv else -1 if a.dis else 0)
            lines.append(f"{a.expr}{lbl} = {total}   {detail}")
        else:
            ap.print_help(); return 1
    for line in lines:
        print(line)
        if not a.no_log:
            log(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
