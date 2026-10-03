#!/usr/bin/env python3
"""Compose an image prompt for a hero, or record a generated portrait.

  portrait_prompt.py arya                      print the prompt and append it to portraits/prompt.md
  portrait_prompt.py arya --print-only
  portrait_prompt.py arya --record 001.png --session 1 --note "first portrait"
"""
from __future__ import annotations
import argparse
import re
import sys
from datetime import date
from common import CHARACTERS, load_character, load_campaign, world, dump_yaml, load_yaml


def compose(h: dict) -> str:
    w = world()
    cid = w.get("active_campaign") or h.get("campaign_origin")
    camp = load_campaign(cid) if cid else {}
    style = (h.get("portrait", {}).get("style_override") or camp.get("art_style", "storybook illustration")).strip()
    ap = h.get("appearance", {}) or {}
    pers = h.get("personality", {}) or {}
    look = ", ".join(f"{k} {v}" for k, v in ap.items() if v and k not in ("colors", "distinguishing", "clothing"))
    who = " ".join(x for x in [ap.get("age"), h.get("species"), h.get("class")] if x) or "hero"
    parts = [f"Portrait of {h.get('name') or 'a hero'}, a {who}."]
    if look:
        parts.append(look.capitalize() + ".")
    if ap.get("clothing"):
        parts.append(f"Wearing {ap['clothing']}.")
    if ap.get("distinguishing"):
        parts.append(f"Distinguishing detail: {ap['distinguishing']}.")
    if ap.get("colors"):
        parts.append(f"Signature colors: {ap['colors']}.")
    gear = [i.get("name").rstrip(".") for i in (h.get("inventory") or []) if i.get("name")][:3]
    if h.get("keepsake"):
        gear.insert(0, h["keepsake"].rstrip("."))
    if gear:
        parts.append("Holding or carrying: " + ", ".join(gear) + ".")
    traits = ", ".join(pers.get("traits") or [])
    if traits:
        parts.append(f"Expression: {traits}.")
    comps = [f"{c.get('name')} the {c.get('kind')}" for c in (h.get("companions") or []) if c.get("name")]
    if comps:
        parts.append("Companion beside them: " + ", ".join(comps) + ".")
    loc = (camp.get("state") or {}).get("location")
    if loc:
        parts.append(f"Setting: {loc}.")
    parts.append(f"Style: {style}")
    parts.append("Composition: waist-up, centered, looking slightly past the viewer, clean background with an "
                 "ornamental border, no text, no watermark. Child-friendly, no weapons pointed at the viewer.")
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("id")
    ap.add_argument("--print-only", action="store_true")
    ap.add_argument("--record", metavar="FILE", help="portrait file name inside portraits/")
    ap.add_argument("--session", type=int, default=0)
    ap.add_argument("--note", default="")
    a = ap.parse_args(argv)
    d = CHARACTERS / a.id
    if not d.exists():
        raise SystemExit(f"No hero {a.id!r}")
    if a.record:
        p = d / "character.yaml"
        c = load_yaml(p)
        rel = f"portraits/{a.record}"
        if not (d / rel).exists():
            raise SystemExit(f"{d / rel} not found; save the image there first")
        c.setdefault("portrait", {})
        c["portrait"]["current"] = rel
        c["portrait"].setdefault("history", []).append(
            {"file": rel, "session": a.session, "date": str(date.today()), "note": a.note})
        dump_yaml(p, c)
        print(f"Recorded {rel} as current portrait for {a.id}.")
        return 0
    h = load_character(a.id)
    prompt = compose(h)
    print(prompt)
    if not a.print_only:
        pf = d / "portraits" / "prompt.md"
        with open(pf, "a", encoding="utf-8") as f:
            f.write(f"\n\n## {date.today()}{' · ' + a.note if a.note else ''}\n\n{prompt}\n")
        print(f"\n(appended to {pf.relative_to(CHARACTERS.parent)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
