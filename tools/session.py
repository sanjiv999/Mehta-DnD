#!/usr/bin/env python3
"""Session helpers.

  session.py prep              print the DM brief for the next session of the active campaign
  session.py new "Title"       create the next session log file from the template
"""
from __future__ import annotations
import argparse
import re
import sys
from datetime import date
from common import CAMPAIGNS, CHARACTERS, load_character, load_campaign, load_md, world, fmt_bonus


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def current_chapter(c):
    for p in sorted((c["dir"] / "chapters").glob("*.md")):
        meta, body = load_md(p)
        if meta.get("number") == c["state"].get("chapter"):
            return meta, body
    return {}, ""


def cmd_prep(_a):
    w = world()
    cid = w.get("active_campaign")
    if not cid:
        raise SystemExit("No active campaign. Run campaign.py switch <id>.")
    c = load_campaign(cid)
    st = c["state"]
    n = len(c["sessions"]) + 1
    print(f"# DM brief: {c['title']}, session {n}\n")
    print(f"**Chapter {st.get('chapter')}: {st.get('chapter_title','')}**  ")
    print(f"Location: {st.get('location','')}  ")
    print(f"World date: {st.get('world_date','')}  ")
    print(f"Party goal: {st.get('party_goal','')}\n")
    if c["sessions"]:
        last = c["sessions"][-1]
        m = re.search(r"## Recap.*?\n(.*?)(?=\n## )", last["body"], re.S)
        print("## Last time\n" + (m.group(1).strip() if m else last.get("title", "")) + "\n")
    print("## Open threads")
    for t in st.get("open_threads", []):
        if t.get("status", "open") == "open":
            print(f"- ({t['id']}) {t['text']}")
    print("\n## Recent events")
    for e in st.get("recent_events", []) or ["(none yet)"]:
        print(f"- {e}")
    print(f"\n## Hook\n{st.get('next_hook','')}\n")
    print("## Heroes")
    for pid in w.get("party", []):
        h = load_character(pid)
        hp = h.get("hp", {})
        ab = h.get("abilities", {})
        name = h.get("name") or f"(unbuilt: {h.get('player')})"
        kids = " [kids mode]" if h.get("kids_mode") else ""
        print(f"- **{name}** ({h.get('player')}){kids}: {h.get('species','')} {h.get('class','')} L{h.get('level',1)}, "
              f"HP {hp.get('current')}/{hp.get('max')}, AC {h.get('ac')}, Hero Points {h.get('hero_points',3)}")
        if ab:
            print("  " + "  ".join(f"{k.upper()} {fmt_bonus(v)}" for k, v in ab.items()))
        if h.get("conditions"):
            print(f"  conditions: {', '.join(h['conditions'])}")
        fears = h.get("personality", {}).get("fears") or []
        dream = h.get("personality", {}).get("dream")
        if fears or dream:
            print(f"  fears: {', '.join(fears) or '-'}; dream: {dream or '-'}")
    meta, body = current_chapter(c)
    if body:
        print(f"\n## Chapter notes\n{body.strip()[:4000]}")
    print("\n## Reputation")
    for k, v in (st.get("reputation") or {}).items():
        print(f"- {k}: {v:+d}")
    print(f"\n_DM-only material: campaigns/{cid}/dm/_")
    return 0


def cmd_new(a):
    w = world()
    cid = w.get("active_campaign")
    c = load_campaign(cid)
    n = len(c["sessions"]) + 1
    tpl = (CAMPAIGNS / "_template" / "sessions" / "000-template.md").read_text(encoding="utf-8")
    text = (tpl.replace("number: 0", f"number: {n}")
               .replace("date: YYYY-MM-DD", f"date: {date.today()}")
               .replace("title: Session Title", f"title: {a.title}")
               .replace("chapter: 1", f"chapter: {c['state'].get('chapter', 1)}")
               .replace("# Session 0: Title", f"# Session {n}: {a.title}")
               .replace("attendees: [sanjiv, vai, aarya, keshu]", f"attendees: {w.get('party', [])}"))
    out = c["dir"] / "sessions" / f"{n:03d}-{slug(a.title)}.md"
    out.write_text(text, encoding="utf-8")
    print(f"Created {out.relative_to(CAMPAIGNS.parent)}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prep").set_defaults(fn=cmd_prep)
    p = sub.add_parser("new"); p.add_argument("title"); p.set_defaults(fn=cmd_new)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
