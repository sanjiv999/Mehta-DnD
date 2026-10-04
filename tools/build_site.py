#!/usr/bin/env python3
"""Render the site into _site/ (public) or, with --dm, into _site_dm/ (the DM screen).

Public build: anything under dm/ or campaigns/*/dm/, any YAML key named `secret`, any Markdown
'## Secret' section, NPCs/locations with `public: false`, chapter DM notes, and decks for planned
chapters are left out. The DM build includes all of it and must never be published.
"""
from __future__ import annotations
import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from common import (ROOT, RULES, TABLES, CAMPAIGNS, load_md, load_yaml, load_character, load_campaign,
                    strip_secrets, strip_secret_section, world, campaign_ids, character_ids, fmt_bonus)
from scenes import chapters as parse_chapters, image_slots, find_image
from placeholder import placeholder_svg

SITE = ROOT / "site"
MD = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "attr_list"])
DM = False


def md(text: str) -> str:
    MD.reset()
    html = MD.convert(text if DM else strip_secret_section(text or ""))
    return html.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")


def secret_section(body: str) -> str:
    m = re.search(r"^##\s+Secret\b(.*)$", body, re.M | re.S)
    return m.group(1).strip() if m else ""


def load_public_md(folder: Path) -> list[dict]:
    out = []
    if not folder.exists():
        return out
    for p in sorted(folder.glob("*.md")):
        if p.name.startswith("_") or p.name.startswith("000"):
            continue
        meta, body = load_md(p)
        if meta.get("public", True) is False and not DM:
            continue
        meta["slug"] = p.stem
        meta["html"] = md(body)
        meta["secret_html"] = MD.convert(secret_section(body)) if DM else ""
        out.append(meta)
    return out


EMOJI = {"sword": "⚔️", "shield": "🛡️", "bow": "🏹", "dagger": "🗡️", "rope": "🪢", "lamp": "🪔", "jar": "🫙", "key": "🔑",
         "map": "🗺️", "coin": "🪙", "pearl": "🫧", "feather": "🪶", "bell": "🔔", "book": "📖", "potion": "🧪", "food": "🍱",
         "mango": "🥭", "pie": "🥧", "kite": "🪁", "drum": "🥁", "scale": "🐉", "charm": "📜", "ofuda": "📜", "hammer": "🔨",
         "cloak": "🧥", "boots": "👢", "mirror": "🪞", "camel": "🐪", "flame": "🔥", "star": "⭐", "stone": "🪨"}


def item_icon(name: str) -> str:
    n = (name or "").lower()
    for k, v in EMOJI.items():
        if k in n:
            return v
    return "🎒"


def main(argv=None) -> int:
    global DM
    ap = argparse.ArgumentParser()
    ap.add_argument("--dm", action="store_true", help="build the DM screen into _site_dm/")
    ap.add_argument("--out", help="output folder (default _site or _site_dm)")
    a = ap.parse_args(argv)
    DM = a.dm
    out = Path(a.out) if a.out else ROOT / ("_site_dm" if DM else "_site")

    env = Environment(loader=FileSystemLoader(SITE / "templates"), autoescape=select_autoescape(["html"]))
    env.filters["md"] = md
    env.filters["bonus"] = fmt_bonus
    env.filters["icon"] = item_icon
    env.filters["raw_md"] = lambda t: MD.convert(t or "")

    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    shutil.copytree(SITE / "static", out / "static")
    (out / ".nojekyll").touch()
    shutil.copy(SITE / "static" / "robots.txt", out / "robots.txt")   # keep the family site out of search engines

    w = world()

    def image_url(cid: str, slot: str, title: str, kind: str, accent: str) -> str:
        """Copy the real image or write a placeholder; return the site-relative path."""
        dest_dir = out / "campaigns" / cid / "images"
        dest_dir.mkdir(parents=True, exist_ok=True)
        src = find_image(cid, slot)
        if src:
            dest = dest_dir / (slot + src.suffix.lower())
            if not dest.exists():
                shutil.copy(src, dest)
            return f"campaigns/{cid}/images/{dest.name}"
        dest = dest_dir / f"{slot}.svg"
        if not dest.exists():
            dest.write_text(placeholder_svg(title, accent, kind), encoding="utf-8")
        return f"campaigns/{cid}/images/{slot}.svg"

    campaigns = {}
    for cid in campaign_ids():
        c = load_campaign(cid)
        c = c if DM else strip_secrets(c)
        accent = c.get("accent_color", "#0f766e")
        c["html"] = md((c["dir"] / "overview.md").read_text(encoding="utf-8")) if (c["dir"] / "overview.md").exists() else ""
        c["npcs"] = load_public_md(c["dir"] / "npcs")
        c["locations"] = load_public_md(c["dir"] / "locations")
        c["cover"] = image_url(cid, "cover", "", "cover", accent)       # no title text: the page shows it
        c["map_image"] = image_url(cid, "map", "", "map", accent)
        for n in c["npcs"]:
            n["image"] = image_url(cid, f"npc-{n['slug']}", n.get("name", n["slug"]), "npc", accent)
        for l in c["locations"]:
            l["image"] = image_url(cid, f"loc-{l['slug']}", l.get("name", l["slug"]), "location", accent)
        chs = parse_chapters(cid)
        for ch in chs:
            n = int(ch.get("number", 0))
            ch["image"] = image_url(cid, f"ch{n:02d}", ch.get("title", ""), "chapter", accent)
            reached = int(c["state"].get("chapter", 0) or 0) >= n and c.get("status") in ("active", "paused", "completed")
            ch["deck"] = DM or ch.get("status") in ("active", "done") or reached
            ch["dm_html"] = MD.convert(ch["dm_md"]) if DM else ""
            for s in ch["scenes"]:
                s["image_url"] = image_url(cid, f"ch{n:02d}-{s['slug']}", f"{ch.get('title','')}: {s['title']}", "scene", accent)
                s["dm_html"] = MD.convert(s["dm_md"]) if DM else ""
        c["chapters"] = chs
        c["hours"] = sum(float(ch.get("hours_estimate", 0) or 0) for ch in chs)
        c["sessions_estimate"] = sum(int(ch.get("sessions_estimate", 0) or 0) for ch in chs)
        for s in c["sessions"]:
            s["html"] = md(s["body"])
            s["image"] = image_url(cid, f"session-{int(s.get('number', 0)):03d}", s.get("title", ""), "scene", accent) \
                if find_image(cid, f"session-{int(s.get('number', 0)):03d}") or s.get("image_prompt") else ""
        side = c["dir"] / "side-quests.md"
        c["side_quests_html"] = md(side.read_text(encoding="utf-8")) if side.exists() else ""
        loc_by = {l["slug"]: l for l in c["locations"]}
        c["map_routes"] = [(loc_by[a_], loc_by[b_]) for a_, b_ in (c.get("map") or {}).get("routes", []) if a_ in loc_by and b_ in loc_by]
        if DM:
            c["dm_pages"] = []
            for p in sorted((c["dir"] / "dm").glob("*.md")):
                if p.name == "README.md":
                    continue
                c["dm_pages"].append({"title": p.stem.title(), "html": MD.convert(p.read_text(encoding="utf-8"))})
            for n in c["npcs"]:
                pass
        campaigns[cid] = c

    heroes = {}
    for hid in character_ids():
        h = load_character(hid)
        h = h if DM else strip_secrets(h)
        h["journal_html"] = md(h["journal"])
        h["in_party"] = hid in (w.get("party") or [])
        h["origin"] = campaigns.get(h.get("campaign_origin"), {})
        pdir = h["dir"] / "portraits"
        h["portrait_files"] = sorted(p.name for p in pdir.glob("*.png")) + sorted(p.name for p in pdir.glob("*.jpg"))
        h.setdefault("portrait", {})
        if not h["portrait"].get("current") and h["portrait_files"]:
            # a picture uploaded through the GitHub website counts even before the sheet is updated
            h["portrait"]["current"] = "portraits/" + h["portrait_files"][-1]
        heroes[hid] = h

    rules = []
    for p in sorted(RULES.glob("*.md")):
        meta, body = load_md(p)
        rules.append({"title": meta.get("title", p.stem), "order": meta.get("order", 99), "slug": p.stem, "html": md(body)})
    rules.sort(key=lambda r: r["order"])

    # story so far: all sessions across campaigns in play order
    story = []
    for ev in w.get("history", []):
        pass
    for cid in w.get("campaign_order", []) or campaign_ids():
        c = campaigns.get(cid)
        if not c:
            continue
        for s in c["sessions"]:
            m = re.search(r"##\s*Recap.*?\n(.*?)(?=\n##\s|\Z)", s["body"], re.S)
            story.append({"campaign": c, "session": s, "recap_html": md(m.group(1).strip() if m else "")})

    # sticker book
    stickers = []
    for hid, h in heroes.items():
        for a_ in h.get("achievements") or []:
            stickers.append({"hero": h, "title": a_.get("title"), "session": a_.get("session"), "note": a_.get("note")})
    for cid, c in campaigns.items():
        for s in c["sessions"]:
            for m in s.get("hero_moments") or []:
                hero = next((h for h in heroes.values() if h.get("name") == m.get("who") or h["id"] == m.get("who")), None)
                stickers.append({"hero": hero, "who": m.get("who"), "title": m.get("what"), "session": s.get("number"), "note": s.get("title"), "campaign": c})

    # tables for the builder
    tables = {}
    for t in TABLES.glob("*.yaml"):
        tb = load_yaml(t)
        tables[t.stem] = [e if isinstance(e, str) else e.get("text") for e in tb.get("entries", [])]
    (out / "static" / "tables.json").write_text(json.dumps(tables, ensure_ascii=False), encoding="utf-8")
    classes_md = (RULES / "classes.md").read_text(encoding="utf-8")

    active = campaigns.get(w.get("active_campaign")) if w.get("active_campaign") else None
    ctx = dict(world=w, campaigns=campaigns, heroes=heroes, active=active, rules=rules, dm=DM, story=story,
               stickers=stickers, built=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
               party=[heroes[p] for p in (w.get("party") or []) if p in heroes],
               resting=[h for hid, h in heroes.items() if hid not in (w.get("party") or [])])

    def render(tpl: str, dest: str, **extra):
        (out / dest).parent.mkdir(parents=True, exist_ok=True)
        depth = dest.count("/")
        (out / dest).write_text(env.get_template(tpl).render(root="../" * depth, page=dest, **ctx, **extra), encoding="utf-8")

    if DM:
        from images import sheet_rows
        render("prompts.html", "prompts.html", prompts=sheet_rows(list(campaigns.keys())))
    render("index.html", "index.html")
    render("dice.html", "dice.html")
    render("rules.html", "rules.html")
    render("story.html", "story.html")
    render("stickers.html", "stickers.html")
    render("build.html", "build.html")
    for hid, h in heroes.items():
        render("character.html", f"characters/{hid}.html", hero=h)
        if (h["dir"] / "portraits").exists():
            dst = out / "characters" / hid / "portraits"
            dst.mkdir(parents=True, exist_ok=True)
            for img in h["portrait_files"]:
                shutil.copy(h["dir"] / "portraits" / img, dst / img)
    for cid, c in campaigns.items():
        render("campaign.html", f"campaigns/{cid}.html", campaign=c)
        for ch in c["chapters"]:
            if ch["deck"]:
                render("deck.html", f"play/{cid}/{int(ch.get('number', 0)):02d}.html", campaign=c, chapter=ch)
    print(f"Built {out.name} ({'DM screen' if DM else 'public'}): {len(heroes)} heroes, {len(campaigns)} campaigns, "
          f"{sum(len(c['chapters']) for c in campaigns.values())} chapters, {sum(1 for c in campaigns.values() for ch in c['chapters'] if ch['deck'])} decks.")
    if not DM and not a.out and w.get("publish_dm_screen"):
        # the DM asked for the DM screen on the public site, at /dm/ (anyone with the link can read the secrets)
        return main(["--dm", "--out", str(out / "dm")])
    return 0


if __name__ == "__main__":
    sys.exit(main())
