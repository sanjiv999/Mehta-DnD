#!/usr/bin/env python3
"""Campaign lifecycle: status, new, start, switch, pause, resume, complete.

  campaign.py status
  campaign.py new <id> "Title"
  campaign.py switch <id>          make <id> active (pauses the current one, starts <id> if planned)
  campaign.py pause  [--note "..."]
  campaign.py resume <id>
  campaign.py complete <id>
"""
from __future__ import annotations
import argparse
import shutil
import sys
from datetime import date
from common import (ROOT, CAMPAIGNS, CHARACTERS, STATE, load_yaml, dump_yaml, world,
                    campaign_ids, load_campaign)


def save_world(w): dump_yaml(STATE, w)


def set_status(cid: str, status: str, **extra):
    p = CAMPAIGNS / cid / "campaign.yaml"
    c = load_yaml(p)
    c["status"] = status
    c.update(extra)
    dump_yaml(p, c)


def history(w, cid, event):
    w.setdefault("history", []).append({"campaign": cid, "event": event, "date": str(date.today()),
                                        "session": w.get("session_counter", 0)})


def crossing_entry(w, src: str, dst: str):
    d = load_campaign(dst)
    s = load_campaign(src) if src else None
    for pid in w.get("party", []):
        j = CHARACTERS / pid / "journal.md"
        if not j.exists():
            continue
        line = (f"\n\n## Crossing: {s['title'] if s else 'the beginning'} → {d['title']} ({date.today()})\n\n"
                f"*How I came through the Door: {str(d.get('door', 'a door between worlds')).rstrip('.')}.*\n"
                f"*(Fill this in. Keepsake carried: see character.yaml.)*\n")
        with open(j, "a", encoding="utf-8") as f:
            f.write(line)


def cmd_status(_a):
    w = world()
    print(f"Active campaign : {w.get('active_campaign')}")
    print(f"Party           : {', '.join(w.get('party', []))}")
    print(f"Sessions played : {w.get('session_counter', 0)}   last: {w.get('last_played')}")
    print(f"Lantern pieces  : {w.get('lantern_pieces', 0)}/4\n")
    for cid in campaign_ids():
        c = load_campaign(cid)
        st = c["state"]
        mark = "▶" if c["status"] == "active" else "‖" if c["status"] == "paused" else "✓" if c["status"] == "completed" else "·"
        print(f"{mark} {cid:16} {c['status']:9} {c['title']}")
        if c["status"] in ("active", "paused"):
            print(f"    chapter {st.get('chapter')}: {st.get('chapter_title','')} @ {st.get('location','')}")
            if st.get("resume_note"):
                print(f"    resume: {st['resume_note']}")
    return 0


def cmd_new(a):
    dst = CAMPAIGNS / a.id
    if dst.exists():
        raise SystemExit(f"{dst} exists")
    shutil.copytree(CAMPAIGNS / "_template", dst)
    c = load_yaml(dst / "campaign.yaml")
    c["id"], c["title"], c["status"] = a.id, a.title, "planned"
    dump_yaml(dst / "campaign.yaml", c)
    (dst / "sessions" / ".gitkeep").touch()
    print(f"Created campaigns/{a.id}/ from template. Edit campaign.yaml and overview.md next.")
    return 0


def cmd_switch(a):
    w = world()
    if a.id not in campaign_ids():
        raise SystemExit(f"No campaign {a.id!r}")
    cur = w.get("active_campaign")
    if cur == a.id:
        print(f"{a.id} is already active."); return 0
    if cur:
        set_status(cur, "paused")
        history(w, cur, "paused")
        print(f"Paused {cur}.")
    dst = load_campaign(a.id)
    if dst["status"] == "planned":
        set_status(a.id, "active", started=str(date.today()))
        history(w, a.id, "started")
    else:
        set_status(a.id, "active")
        history(w, a.id, "resumed")
    w["active_campaign"] = a.id
    save_world(w)
    crossing_entry(w, cur, a.id)
    print(f"Active campaign is now {a.id}. Crossing stubs added to party journals.")
    return 0


def cmd_pause(a):
    w = world()
    cur = w.get("active_campaign")
    if not cur:
        raise SystemExit("No active campaign")
    set_status(cur, "paused")
    sp = CAMPAIGNS / cur / "state.yaml"
    s = load_yaml(sp)
    if a.note:
        s["resume_note"] = a.note
    dump_yaml(sp, s)
    history(w, cur, "paused")
    w["active_campaign"] = None
    save_world(w)
    print(f"Paused {cur}. No campaign is active; use `switch` or `resume`.")
    return 0


def cmd_resume(a):
    return cmd_switch(a)


def cmd_complete(a):
    w = world()
    set_status(a.id, "completed")
    history(w, a.id, "completed")
    w["lantern_pieces"] = min(4, int(w.get("lantern_pieces", 0)) + 1)
    if w.get("active_campaign") == a.id:
        w["active_campaign"] = None
    save_world(w)
    print(f"Completed {a.id}. Lantern pieces: {w['lantern_pieces']}/4.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    p = sub.add_parser("new"); p.add_argument("id"); p.add_argument("title"); p.set_defaults(fn=cmd_new)
    p = sub.add_parser("switch"); p.add_argument("id"); p.set_defaults(fn=cmd_switch)
    p = sub.add_parser("pause"); p.add_argument("--note", default=""); p.set_defaults(fn=cmd_pause)
    p = sub.add_parser("resume"); p.add_argument("id"); p.set_defaults(fn=cmd_resume)
    p = sub.add_parser("complete"); p.add_argument("id"); p.set_defaults(fn=cmd_complete)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
