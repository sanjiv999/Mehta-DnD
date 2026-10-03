#!/usr/bin/env python3
"""Interactive hero builder that follows characters/GUIDE.md and writes characters/<id>/.

Run it at the table with a kid beside you. Every question can be skipped with Enter.
"""
from __future__ import annotations
import re
import shutil
import sys
from common import CHARACTERS, ROOT, load_yaml, dump_yaml, TABLES, bonus
import random

CLASSES = {
    "warrior": ("d10", 10), "ranger": ("d10", 10), "rogue": ("d8", 8), "mage": ("d6", 6),
    "priest": ("d8", 8), "sage": ("d8", 8), "bard": ("d8", 8), "beast-friend": ("d8", 8), "inventor": ("d8", 8),
}
ARRAY = [15, 14, 13, 12, 10, 8]
ABILS = ["str", "dex", "con", "int", "wis", "cha"]


def ask(q: str, default: str = "") -> str:
    try:
        v = input(f"{q}{f' [{default}]' if default else ''}: ").strip()
    except EOFError:
        return default
    return v or default


def ask_list(q: str) -> list[str]:
    v = ask(q + " (comma separated)")
    return [s.strip() for s in v.split(",") if s.strip()]


def suggest(table: str, n=3):
    t = load_yaml(TABLES / f"{table}.yaml")
    picks = random.sample(t["entries"], min(n, len(t["entries"])))
    print("  Ideas:")
    for p in picks:
        print("   •", p if isinstance(p, str) else p.get("text"))


def main() -> int:
    print("Let's make a hero! Press Enter to skip any question.\n")
    player = ask("Who is playing (real name)")
    cid = ask("Short id for the folder (lowercase)", re.sub(r"[^a-z0-9]+", "-", player.lower()).strip("-"))
    kids = ask("Kids mode? (y/n)", "n").lower().startswith("y")
    dst = CHARACTERS / cid
    if dst.exists() and (dst / "character.yaml").exists():
        c = load_yaml(dst / "character.yaml")
        print(f"(editing existing hero {cid})")
    else:
        shutil.copytree(CHARACTERS / "_template", dst, dirs_exist_ok=True)
        c = load_yaml(dst / "character.yaml")
    c["id"], c["player"], c["kids_mode"] = cid, player, kids

    print("\n— Part 1: the spark —")
    suggest("hero-seeds")
    c["species"] = ask("What kind of creature or person are you?", "Human")
    cool = ask("What is the coolest thing you can do?")
    c["personality"]["loves"] = ask_list("Who or what do you love most?")
    c["personality"]["fears"] = ask_list("What are you a little scared of?")
    c["personality"]["dream"] = ask("What do you want more than anything?")
    c["name"] = ask("What is your hero's name?")
    c["concept"] = ask("One exciting sentence about your hero", f"{c['name']} the {c['species']} who {cool}")

    print("\n— Part 2: shape —")
    c["appearance"]["hair"] = ask("Hair")
    c["appearance"]["eyes"] = ask("Eyes")
    c["appearance"]["clothing"] = ask("Clothes")
    c["appearance"]["colors"] = ask("Favourite colours")
    c["appearance"]["distinguishing"] = ask("One special detail (scar, pet on shoulder, glowing hands...)")
    c["appearance"]["age"] = ask("How old does your hero look?")
    suggest("powers-kids")
    powers = []
    for i in range(3):
        nm = ask(f"Power {i+1} name")
        if not nm:
            break
        powers.append({"name": nm, "kid_name": nm if kids else "", "description": ask("  what does it do?"),
                       "uses": ask("  how often?", "1 per short rest"), "source": "player"})
    c["powers"] = powers
    suggest("keepsakes")
    c["keepsake"] = ask("One treasure you already own (your keepsake)")
    cls = ask(f"Class ({', '.join(CLASSES)})", "warrior").lower()
    c["class"] = cls.capitalize()
    die, base = CLASSES.get(cls, ("d8", 8))
    c["hit_dice"] = die
    print(f"Assign {ARRAY} to {', '.join(a.upper() for a in ABILS)}. Highest to the coolest thing.")
    remaining = ARRAY[:]
    for a in ABILS:
        v = ask(f"  {a.upper()} (left: {remaining})", str(remaining[0]))
        v = int(v) if v.isdigit() and int(v) in remaining else remaining[0]
        remaining.remove(v)
        c["abilities"][a] = v
    c["hp"] = {"max": base + bonus(c["abilities"]["con"]), "current": base + bonus(c["abilities"]["con"])}
    c["ac"] = 10 + bonus(c["abilities"]["dex"]) + (1 if cls in ("warrior", "ranger") else 0)
    c["trained_skills"] = ask_list("Four trained skills")
    c["personality"]["traits"] = ask_list("Three words that describe your hero")

    print("\n— Part 3: story —")
    home = ask("Where do you come from? (one place, one smell, one sound)")
    why = ask("Why did you leave?")
    knows = ask("Who in the party do you already know, and how?")
    c["backstory"] = f"{home} {why} {knows}".strip()
    c["status"] = "active" if ask("Happy with this hero? (y/n)", "y").lower().startswith("y") else "draft"
    c["inventory"] = c.get("inventory") or []
    dump_yaml(dst / "character.yaml", c)
    (dst / "journal.md").write_text(
        f"# Journal of {c['name']}\n\n<!-- First-person entries in the hero's voice. Newest at the bottom. -->\n\n"
        f"## Before the story (Session 0)\n\n{c['backstory'] or '*To be written.*'}\n", encoding="utf-8")
    print(f"\nSaved characters/{cid}/. Next: add '{cid}' to party in state/world.yaml, then "
          f"python tools/portrait_prompt.py {cid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
