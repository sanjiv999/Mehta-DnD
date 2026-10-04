#!/usr/bin/env python3
"""Automated session ingest: turn a transcript into a session log, state updates and journal
entries using Claude, then apply them to the repository files.

  python tools/ingest.py dm/transcripts/001-2026-10-12.md            # active campaign, next session number
  python tools/ingest.py <file> --campaign peacock-throne --number 3 --dry-run

Needs the `anthropic` package and ANTHROPIC_API_KEY (or an `ant auth login` profile).
The interactive route (asking Claude Code to ingest, per CLAUDE.md) remains the richer option;
this script is the "drop a file, get a pull request" path used by the ingest workflow.
"""
from __future__ import annotations
import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import List, Optional

import anthropic
from pydantic import BaseModel, Field

from common import ROOT, CAMPAIGNS, CHARACTERS, STATE, load_yaml, dump_yaml, world, load_campaign, load_character
from scenes import chapters

MODEL = "claude-opus-5-5"


class HeroMoment(BaseModel):
    who: str
    what: str


class Thread(BaseModel):
    id: str
    text: str
    status: str = Field(description="open or resolved")


class HeroUpdate(BaseModel):
    id: str
    hp_current: Optional[int] = None
    xp_add: int = 0
    level: Optional[int] = None
    inventory_add: List[str] = []
    inventory_remove: List[str] = []
    conditions: Optional[List[str]] = None
    relationships_add: List[str] = Field(default=[], description="'who | feeling | note'")
    achievements_add: List[str] = Field(default=[], description="short badge titles")
    journal_entry: str = Field(description="first person, in the hero's voice, 3-6 sentences")
    look_changed: bool = False
    portrait_prompt_addendum: str = ""


class SessionIngest(BaseModel):
    title: str
    recap: str = Field(description="second person, three sentences, to read aloud next time")
    what_happened_md: str = Field(description="third person past tense Markdown with ### sub-headings per scene")
    state_changes_md: str
    dm_feedback_md: str = Field(description="pacing, what each player enjoyed, loose ends, three ideas, any child who seemed unsure")
    hero_moments: List[HeroMoment] = []
    loot: List[str] = []
    image_prompt: str = Field(description="one line describing the session's best moment for an illustration")
    chapter: int
    chapter_title: str
    location: str
    location_id: str = ""
    world_date: str
    party_goal: str
    open_threads: List[Thread]
    recent_events: List[str] = Field(description="the last five notable events including tonight's")
    next_hook: str
    heroes: List[HeroUpdate]
    unclear: List[str] = Field(default=[], description="things the transcript left ambiguous")


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:50]


def build_context(cid: str, n: int) -> str:
    c = load_campaign(cid)
    st = c["state"]
    parts = [f"# Campaign: {c['title']}\n{c.get('tagline','')}\n",
             "## Current state (campaigns/%s/state.yaml)\n```yaml\n%s```" % (cid, Path(CAMPAIGNS / cid / 'state.yaml').read_text())]
    for ch in chapters(cid):
        if ch.get("number") == st.get("chapter"):
            parts.append(f"## Current chapter file\n{ch['body'][:12000]}")
    for pid in world().get("party", []):
        h = load_character(pid)
        parts.append(f"## Hero {pid} (characters/{pid}/character.yaml)\n```yaml\n{(CHARACTERS / pid / 'character.yaml').read_text()}```")
    parts.append("## Rules summary\n" + (ROOT / "rules" / "family-rules.md").read_text()[:4000])
    parts.append("## Ingest instructions\n" + (ROOT / "dm" / "prompts" / "session-ingest.md").read_text())
    return "\n\n".join(parts)


def apply(cid: str, n: int, r: SessionIngest, transcript_name: str, dry: bool) -> list[str]:
    changed = []
    c = load_campaign(cid)
    w = world()
    attendees = w.get("party", [])
    fm = {"number": n, "date": str(date.today()), "title": r.title, "chapter": r.chapter, "attendees": attendees,
          "xp_awarded": {h.id: h.xp_add for h in r.heroes}, "loot": r.loot,
          "hero_moments": [m.model_dump() for m in r.hero_moments],
          "portrait_updates": [h.id for h in r.heroes if h.look_changed],
          "image_prompt": r.image_prompt, "transcript": transcript_name}
    import yaml as _y
    log = ("---\n" + _y.safe_dump(fm, sort_keys=False, allow_unicode=True) + "---\n"
           f"# Session {n}: {r.title}\n\n## Recap (read aloud next time)\n{r.recap}\n\n## What happened\n{r.what_happened_md}\n\n"
           f"## State changes\n{r.state_changes_md}\n\n## DM feedback\n{r.dm_feedback_md}\n")
    if r.unclear:
        log += "\n## Unclear from the transcript\n" + "\n".join(f"- {u}" for u in r.unclear) + "\n"
    out = CAMPAIGNS / cid / "sessions" / f"{n:03d}-{slug(r.title)}.md"
    changed.append(str(out))
    if not dry:
        out.write_text(log, encoding="utf-8")

    sp = CAMPAIGNS / cid / "state.yaml"
    st = load_yaml(sp)
    st.update(chapter=r.chapter, chapter_title=r.chapter_title, location=r.location, world_date=r.world_date,
              party_goal=r.party_goal, open_threads=[t.model_dump() for t in r.open_threads],
              recent_events=r.recent_events[-5:], next_hook=r.next_hook)
    if r.location_id:
        st["location_id"] = r.location_id
    changed.append(str(sp))
    if not dry:
        dump_yaml(sp, st)
        cp = CAMPAIGNS / cid / "campaign.yaml"
        cm = load_yaml(cp); cm["sessions_played"] = int(cm.get("sessions_played", 0)) + 1
        cm.setdefault("started", str(date.today())); dump_yaml(cp, cm)

    for h in r.heroes:
        d = CHARACTERS / h.id
        if not d.exists():
            continue
        p = d / "character.yaml"
        ch = load_yaml(p)
        if h.hp_current is not None:
            ch["hp"]["current"] = max(0, min(int(h.hp_current), int(ch["hp"]["max"])))
        ch["xp"] = int(ch.get("xp", 0)) + int(h.xp_add)
        if h.level:
            ch["level"] = int(h.level)
        for item in h.inventory_add:
            ch.setdefault("inventory", []).append({"name": item, "qty": 1, "notes": f"session {n}"})
        if h.inventory_remove:
            ch["inventory"] = [i for i in ch.get("inventory", []) if i.get("name") not in h.inventory_remove]
        if h.conditions is not None:
            ch["conditions"] = h.conditions
        for rel in h.relationships_add:
            bits = [b.strip() for b in rel.split("|")] + ["", ""]
            ch.setdefault("relationships", []).append({"who": bits[0], "campaign": cid, "feeling": bits[1], "note": bits[2]})
        for a in h.achievements_add:
            ch.setdefault("achievements", []).append({"title": a, "session": n, "note": r.title})
        changed.append(str(p))
        if not dry:
            dump_yaml(p, ch)
            with open(d / "journal.md", "a", encoding="utf-8") as f:
                f.write(f"\n\n## Session {n}: {r.title} ({date.today()})\n\n{h.journal_entry.strip()}\n")
            if h.look_changed and h.portrait_prompt_addendum:
                with open(d / "portraits" / "prompt.md", "a", encoding="utf-8") as f:
                    f.write(f"\n\n## {date.today()} · after session {n}\n\n{h.portrait_prompt_addendum.strip()}\n")

    w["session_counter"] = int(w.get("session_counter", 0)) + 1
    w["last_played"] = str(date.today())
    changed.append(str(STATE))
    if not dry:
        dump_yaml(STATE, w)
    return changed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript")
    ap.add_argument("--campaign")
    ap.add_argument("--number", type=int)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    w = world()
    cid = a.campaign or w.get("active_campaign") or sys.exit("No active campaign")
    c = load_campaign(cid)
    n = a.number or (len(c["sessions"]) + 1)
    text = Path(a.transcript).read_text(encoding="utf-8")

    client = anthropic.Anthropic()
    system = ("You are the co-Dungeon Master for a family tabletop game (players include a 7 and a 5 year old). "
              "You turn a messy session transcript into accurate, family-friendly, consistent game records. "
              "Never invent events that did not happen; list ambiguities in `unclear`. Journals must sound like each hero. "
              "Kids Mode heroes get short words and at most one exclamation mark.")
    prompt = build_context(cid, n) + f"\n\n# Transcript of session {n}\n\n{text}\n\nProduce the ingest record."
    print(f"Ingesting {a.transcript} as session {n} of {cid} with {MODEL}...")
    resp = client.messages.parse(model=MODEL, max_tokens=16000, system=system,
                                 output_config={"effort": "high"},
                                 messages=[{"role": "user", "content": prompt}],
                                 output_format=SessionIngest)
    if resp.stop_reason == "refusal":
        sys.exit(f"Model declined: {getattr(resp.stop_details, 'explanation', '')}")
    r = resp.parsed_output
    changed = apply(cid, n, r, Path(a.transcript).name, a.dry_run)
    print(("Would change" if a.dry_run else "Changed") + ":\n  " + "\n  ".join(changed))
    if r.unclear:
        print("\nUnclear:\n  " + "\n  ".join(r.unclear))
    if not a.dry_run:
        Path(a.transcript).with_suffix(".ingested").write_text(f"session {n} {cid} {date.today()}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
