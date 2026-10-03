#!/usr/bin/env python3
"""Render the GitHub Pages site into _site/ from the YAML and Markdown sources.

Only player-safe content is rendered: anything under dm/ or campaigns/*/dm/, any YAML key
named `secret`, any Markdown '## Secret' section, and any NPC/location with `public: false`
is left out.
"""
from __future__ import annotations
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from common import (ROOT, RULES, load_md, load_character, load_campaign, strip_secrets,
                    strip_secret_section, world, campaign_ids, character_ids, fmt_bonus)

SITE = ROOT / "site"
OUT = ROOT / "_site"
MD = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "attr_list"])


def md(text: str) -> str:
    MD.reset()
    return MD.convert(strip_secret_section(text or ""))


def load_public_md(folder: Path) -> list[dict]:
    out = []
    if not folder.exists():
        return out
    for p in sorted(folder.glob("*.md")):
        if p.name.startswith("_") or p.name.startswith("000"):
            continue
        meta, body = load_md(p)
        if meta.get("public", True) is False:
            continue
        meta["slug"] = p.stem
        meta["html"] = md(body)
        out.append(meta)
    return out


def main() -> int:
    env = Environment(loader=FileSystemLoader(SITE / "templates"), autoescape=select_autoescape(["html"]))
    env.filters["md"] = md
    env.filters["bonus"] = fmt_bonus

    w = world()
    campaigns = {}
    for cid in campaign_ids():
        c = strip_secrets(load_campaign(cid))
        c["html"] = md((c["dir"] / "overview.md").read_text(encoding="utf-8")) if (c["dir"] / "overview.md").exists() else ""
        c["npcs"] = load_public_md(c["dir"] / "npcs")
        c["locations"] = load_public_md(c["dir"] / "locations")
        c["chapters"] = load_public_md(c["dir"] / "chapters")
        for ch in c["chapters"]:
            ch["html"] = ""  # chapter bodies are DM material; only titles/status are public
        for s in c["sessions"]:
            s["html"] = md(s["body"])
        campaigns[cid] = c

    heroes = {}
    for hid in character_ids():
        h = strip_secrets(load_character(hid))
        h["journal_html"] = md(h["journal"])
        h["in_party"] = hid in (w.get("party") or [])
        h["origin"] = campaigns.get(h.get("campaign_origin"), {})
        pdir = h["dir"] / "portraits"
        h["portrait_files"] = sorted(p.name for p in pdir.glob("*.png")) + sorted(p.name for p in pdir.glob("*.jpg"))
        heroes[hid] = h

    rules = []
    for p in sorted(RULES.glob("*.md")):
        meta, body = load_md(p)
        rules.append({"title": meta.get("title", p.stem), "order": meta.get("order", 99), "slug": p.stem, "html": md(body)})
    rules.sort(key=lambda r: r["order"])

    active = campaigns.get(w.get("active_campaign")) if w.get("active_campaign") else None
    ctx = dict(world=w, campaigns=campaigns, heroes=heroes, active=active, rules=rules,
               built=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
               party=[heroes[p] for p in (w.get("party") or []) if p in heroes],
               resting=[h for hid, h in heroes.items() if hid not in (w.get("party") or [])])

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(SITE / "static", OUT / "static")
    (OUT / ".nojekyll").touch()

    def render(tpl: str, dest: str, **extra):
        (OUT / dest).parent.mkdir(parents=True, exist_ok=True)
        depth = dest.count("/")
        (OUT / dest).write_text(env.get_template(tpl).render(root="../" * depth, page=dest, **ctx, **extra), encoding="utf-8")

    render("index.html", "index.html")
    render("dice.html", "dice.html")
    render("rules.html", "rules.html")
    for hid, h in heroes.items():
        render("character.html", f"characters/{hid}.html", hero=h)
        if (h["dir"] / "portraits").exists():
            dst = OUT / "characters" / hid / "portraits"
            dst.mkdir(parents=True, exist_ok=True)
            for img in h["portrait_files"]:
                shutil.copy(h["dir"] / "portraits" / img, dst / img)
    for cid, c in campaigns.items():
        render("campaign.html", f"campaigns/{cid}.html", campaign=c)
    print(f"Built {OUT} with {len(heroes)} heroes and {len(campaigns)} campaigns.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
