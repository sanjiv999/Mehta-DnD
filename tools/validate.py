#!/usr/bin/env python3
"""Validate every YAML and Markdown data file. Exit 1 on problems."""
from __future__ import annotations
import sys
from common import (CAMPAIGNS, CHARACTERS, TABLES, load_yaml, load_md, world,
                    campaign_ids, character_ids)

CHAR_REQUIRED = ["id", "player", "name", "status", "kids_mode", "level", "xp", "abilities", "hp", "ac",
                 "powers", "inventory", "appearance", "personality", "portrait"]
CAMP_REQUIRED = ["id", "title", "tagline", "setting", "status", "accent_color", "art_style", "level_range"]
STATE_REQUIRED = ["chapter", "location", "open_threads", "recent_events", "next_hook"]
STATUSES_CHAR = {"draft", "active", "resting", "retired"}
STATUSES_CAMP = {"planned", "active", "paused", "completed"}


def main() -> int:
    problems: list[str] = []

    w = world()
    cids, chids = campaign_ids(), character_ids()
    if w.get("active_campaign") not in cids:
        problems.append(f"world.yaml: active_campaign {w.get('active_campaign')!r} is not a campaign folder")
    for pid in w.get("party", []):
        if pid not in chids:
            problems.append(f"world.yaml: party member {pid!r} has no characters/{pid}/ folder")

    for cid in chids:
        p = CHARACTERS / cid / "character.yaml"
        try:
            c = load_yaml(p)
        except Exception as e:  # noqa: BLE001
            problems.append(f"{p}: YAML error {e}"); continue
        for k in CHAR_REQUIRED:
            if k not in c:
                problems.append(f"{p}: missing {k}")
        if c.get("id") != cid:
            problems.append(f"{p}: id {c.get('id')!r} != folder {cid!r}")
        if c.get("status") not in STATUSES_CHAR:
            problems.append(f"{p}: bad status {c.get('status')!r}")
        ab = c.get("abilities", {})
        for k in ["str", "dex", "con", "int", "wis", "cha"]:
            v = ab.get(k)
            if not isinstance(v, int) or not 1 <= v <= 30:
                problems.append(f"{p}: abilities.{k} = {v!r}")
        hp = c.get("hp", {})
        if not isinstance(hp, dict) or "max" not in hp or "current" not in hp:
            problems.append(f"{p}: hp needs max and current")
        elif hp["current"] > hp["max"]:
            problems.append(f"{p}: hp.current > hp.max")
        if c.get("status") == "active" and not c.get("name"):
            problems.append(f"{p}: active hero has no name")
        cur = c.get("portrait", {}).get("current")
        if cur and not (CHARACTERS / cid / cur).exists():
            problems.append(f"{p}: portrait.current {cur!r} not found")
        if c.get("campaign_origin") and c["campaign_origin"] not in cids:
            problems.append(f"{p}: campaign_origin {c['campaign_origin']!r} unknown")
        if not (CHARACTERS / cid / "journal.md").exists():
            problems.append(f"characters/{cid}: journal.md missing")

    active = 0
    for cid in cids:
        d = CAMPAIGNS / cid
        p = d / "campaign.yaml"
        if not p.exists():
            problems.append(f"{d}: campaign.yaml missing"); continue
        c = load_yaml(p)
        for k in CAMP_REQUIRED:
            if k not in c:
                problems.append(f"{p}: missing {k}")
        if c.get("id") != cid:
            problems.append(f"{p}: id {c.get('id')!r} != folder {cid!r}")
        if c.get("status") not in STATUSES_CAMP:
            problems.append(f"{p}: bad status {c.get('status')!r}")
        if c.get("status") == "active":
            active += 1
            if w.get("active_campaign") != cid:
                problems.append(f"{p}: status active but world.active_campaign is {w.get('active_campaign')!r}")
        sp = d / "state.yaml"
        if not sp.exists():
            problems.append(f"{d}: state.yaml missing")
        else:
            s = load_yaml(sp)
            for k in STATE_REQUIRED:
                if k not in s:
                    problems.append(f"{sp}: missing {k}")
            for t in s.get("open_threads", []):
                if not isinstance(t, dict) or "id" not in t or "text" not in t:
                    problems.append(f"{sp}: thread {t!r} needs id and text")
        for sub in ["npcs", "locations", "chapters", "sessions"]:
            for md in (d / sub).glob("*.md") if (d / sub).exists() else []:
                if md.name.startswith("_") or md.name.startswith("000"):
                    continue
                try:
                    meta, _ = load_md(md)
                except Exception as e:  # noqa: BLE001
                    problems.append(f"{md}: front matter error {e}"); continue
                if sub == "sessions":
                    for k in ["number", "date", "title", "attendees"]:
                        if k not in meta:
                            problems.append(f"{md}: missing {k}")
                    for a in meta.get("attendees", []):
                        if a not in chids:
                            problems.append(f"{md}: attendee {a!r} unknown")
                elif sub == "chapters" and "number" not in meta:
                    problems.append(f"{md}: missing number")
                elif sub in ("npcs", "locations") and "name" not in meta:
                    problems.append(f"{md}: missing name")
    if active > 1:
        problems.append(f"{active} campaigns are marked active; only one may be")

    for t in TABLES.glob("*.yaml"):
        tb = load_yaml(t)
        if not tb.get("entries"):
            problems.append(f"{t}: no entries")

    if problems:
        print("\n".join(f"  ✗ {p}" for p in problems))
        print(f"\n{len(problems)} problem(s).")
        return 1
    print(f"✓ {len(chids)} heroes, {len(cids)} campaigns, {len(list(TABLES.glob('*.yaml')))} tables: all valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
