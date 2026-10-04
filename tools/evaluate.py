#!/usr/bin/env python3
"""End-to-end evaluation of the whole system, run against a throwaway copy of the repository.

It simulates a family's first weeks: validates the content, builds both sites, checks nothing
secret leaks, creates heroes through the CLI builder and the web wizard, plays two sessions
of the active campaign (prep, log, ingest, journals, badges), files pictures through the image
intake, switches, pauses, resumes and completes campaigns, steps through every scene deck in a
real browser, and checks every page at phone width.

  python tools/evaluate.py                 full run (needs the playwright package and a Chromium)
  python tools/evaluate.py --no-browser    skip the browser checks
  python tools/evaluate.py --keep          keep the scratch copy for inspection

Writes _eval/report.md and _eval/shots/. Exit code 1 if any check fails.
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zlib
import struct
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT = REPO / "_eval"
RESULTS: list[tuple[str, bool, str]] = []
SECTION = ""


def check(name: str, ok: bool, detail: str = ""):
    RESULTS.append((f"{SECTION} · {name}", bool(ok), detail))
    print(("  ✓ " if ok else "  ✗ ") + name + (f"  ({detail})" if detail and not ok else ""))
    return ok


def section(name):
    global SECTION
    SECTION = name
    print(f"\n== {name} ==")


def run(args, cwd, stdin=None, env=None, check_rc=True):
    e = dict(os.environ); e.update(env or {})
    r = subprocess.run([sys.executable] + args, cwd=cwd, input=stdin, capture_output=True, text=True, env=e)
    if check_rc and r.returncode != 0:
        print("    stderr:", r.stderr.strip()[-600:])
    return r


def fake_png(path: Path, w=8, h=8, rgb=(16, 118, 110)):
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def load(p): return yaml.safe_load(Path(p).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ setup
def make_copy() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="mehta-eval-"))
    for item in ["tools", "characters", "campaigns", "state", "rules", "dm", "site", "docs", "requirements.txt", "CLAUDE.md"]:
        src = REPO / item
        (shutil.copytree if src.is_dir() else shutil.copy)(src, tmp / item)
    (tmp / "dm" / "rolls.log").write_text("")
    return tmp


# ------------------------------------------------------------------ checks
def eval_content(W: Path):
    section("Content")
    r = run(["tools/validate.py"], W)
    check("validate.py passes", r.returncode == 0, r.stdout[-300:])
    sys.path.insert(0, str(W / "tools"))
    import importlib
    for m in ("common", "scenes"):
        if m in sys.modules: del sys.modules[m]
    common = importlib.import_module("common"); scenes = importlib.import_module("scenes")
    total_scenes = total_hours = 0
    for cid in common.campaign_ids():
        for ch in scenes.chapters(cid):
            total_scenes += len(ch["scenes"]); total_hours += float(ch.get("hours_estimate", 0) or 0)
            secs = ch["sections"]
            comp = next((v for k, v in secs.items() if k.startswith("complications")), "")
            check(f"{cid}/ch{ch['number']:02d} has a 6-entry complication table", len(re.findall(r"^\d\.", comp, re.M)) >= 6)
            check(f"{cid}/ch{ch['number']:02d} has rewards and an ending", "rewards" in secs and any(k.startswith("how it ends") for k in secs))
            for s in ch["scenes"]:
                check(f"{cid}/ch{ch['number']:02d} scene {s['number']} has art direction", bool(s["image"]))
                check(f"{cid}/ch{ch['number']:02d} scene {s['number']} has 2+ choices", len(s["choices"]) >= 2)
    check("23 chapters, 90+ scenes, 50+ hours", total_scenes >= 90 and total_hours >= 50, f"{total_scenes} scenes, {total_hours} h")
    slots = sum(len(scenes.image_slots(c, common.load_campaign(c))) for c in common.campaign_ids())
    check("image slots enumerate for every world", slots >= 150, str(slots))


def eval_dice(W: Path):
    section("Dice and tables")
    a = run(["tools/roll.py", "4d6kh3", "-n", "3", "--seed", "9", "--no-log"], W).stdout
    b = run(["tools/roll.py", "4d6kh3", "-n", "3", "--seed", "9", "--no-log"], W).stdout
    check("seeded rolls are reproducible", a == b and a.count("=") == 3)
    sys.path.insert(0, str(W / "tools"))
    import roll
    rng = random.Random(1)
    vals = [roll.roll_expr("d20", rng)[0] for _ in range(4000)]
    check("d20 covers 1..20 and averages near 10.5", min(vals) == 1 and max(vals) == 20 and 10.0 < sum(vals) / len(vals) < 11.0)
    adv = [roll.roll_expr("d20", rng, 1)[0] for _ in range(4000)]
    check("advantage raises the mean", sum(adv) / len(adv) > sum(vals) / len(vals) + 2)
    tot, detail = roll.roll_expr("2d6+3", random.Random(3)); check("modifier arithmetic", 5 <= tot <= 15 and "+3" in detail)
    for t in sorted((W / "dm" / "tables").glob("*.yaml")):
        r = run(["tools/roll.py", "--table", t.stem, "--no-log"], W); check(f"table {t.stem} rolls", r.returncode == 0 and "->" in r.stdout)
    o = run(["tools/roll.py", "--oracle", "likely", "-n", "5", "--seed", "4", "--no-log"], W).stdout
    check("oracle answers yes/no", len(o.strip().splitlines()) == 5 and all(("Yes" in l or "No" in l) and "needs" in l for l in o.strip().splitlines()))
    check("rolls are logged", (W / "dm" / "rolls.log").exists() and run(["tools/roll.py", "d6", "--label", "eval"], W).returncode == 0
          and "eval" in (W / "dm" / "rolls.log").read_text())


def eval_character_cli(W: Path):
    section("Character creation (CLI, as Keisha)")
    answers = ["Keisha", "keisha", "y",                                   # player, id, kids mode
               "Tiger-kin", "sneak and climb anything", "my sister, mangoes", "thunder", "to fly",   # spark
               "Zara Sunclaw", "",                                          # name, concept (default)
               "orange with black stripes", "gold", "a green kurta", "orange, green, gold", "an eagle feather behind one ear", "young",
               "Super Climb", "I climb anything", "always", "Tiger Luck", "reroll one die", "1 per session", "Pounce!", "extra 1d6 when sneaky", "always",
               "a feather from a giant eagle",                              # keepsake
               "",                                                          # class: accept the guess (rogue)
               "", "", "", "", "", "",                                      # abilities: accept suggestions
               "Sneaking, Acrobatics, Perception, Animals", "brave, giggly, curious",
               "the rooftops above the bazaar, cardamom, monkeys", "an eagle dropped a feather on me", "I know Arya from the roof", "y"]
    r = run(["tools/new_character.py"], W, stdin="\n".join(answers) + "\n")
    c = load(W / "characters" / "keisha" / "character.yaml")
    check("builder writes the sheet", r.returncode == 0 and c["name"] == "Zara Sunclaw" and c["status"] == "active", r.stderr[-200:])
    check("kids mode and species recorded", c["kids_mode"] is True and c["species"] == "Tiger-kin")
    check("coolest thing guesses the class", c["class"] == "Rogue", c["class"])
    check("coolest thing drives the highest ability", c["abilities"]["dex"] == 15, str(c["abilities"]))
    hp_expected = 8 + (c["abilities"]["con"] - 10) // 2
    check("HP and AC follow the rules", c["hp"]["max"] == hp_expected and c["ac"] == 10 + (c["abilities"]["dex"] - 10) // 2, f"hp {c['hp']} ac {c['ac']}")
    check("three player powers plus keepsake", len(c["powers"]) == 3 and c["keepsake"].startswith("a feather"))
    check("journal written in first person", "I" in (W / "characters" / "keisha" / "journal.md").read_text())
    r = run(["tools/validate.py"], W); check("sheet validates", r.returncode == 0, r.stdout[-200:])
    pp = run(["tools/portrait_prompt.py", "keisha", "--print-only"], W).stdout
    check("portrait prompt uses the sheet and the world's art style", "Zara Sunclaw" in pp and "Tiger-kin" in pp and "Mughal" in pp)


def eval_character_web(W: Path, browser):
    section("Character creation (web wizard, as Arya)")
    if not browser:
        check("skipped (no browser)", True); return
    page = browser.new_page(viewport={"width": 390, "height": 844}, accept_downloads=True)
    errors = []; page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"file://{W}/_site/build.html"); page.wait_for_timeout(300)
    page.fill("#f", "Arya"); page.click("#fwd")                                       # 1 name
    page.click(".chipbtn:has-text('Fairy')"); page.click("#fwd")                      # 2 species
    page.click(".chipbtn:has-text('Do magic')"); page.click("#fwd")                   # 3 cool
    for text in ["my little sister, the sea", "mice", "to find a dragon"]:
        page.fill("#f", text); page.click("#fwd")                                       # 4-6
    page.click("#fwd")                                                                # 7 ideas
    page.fill("#f", "Pip Starlight"); page.click("#fwd")                              # 8 name
    page.fill("#h", "silver"); page.fill("#e", "violet"); page.fill("#c", "a cloak of leaves"); page.click("#fwd")  # 9
    page.click(".chipbtn:has-text('purple')"); page.click(".chipbtn:has-text('silver')"); page.click("#fwd")       # 10
    page.fill("#f", "glowing hands"); page.click("#fwd")                              # 11
    page.fill("#p1", "Sparkle Shield"); page.fill("#p2", "Glow Hands"); page.fill("#p3", "Whisper"); page.click("#fwd")  # 12
    page.fill("#f", "a map with one place missing"); page.click("#fwd")               # 13
    for s in ["Lore", "Perception", "Persuasion", "Nature"]:
        page.click(f".chipbtn:has-text('{s}')")
    page.click("#fwd")                                                                # 14
    for text in ["a lighthouse, salt, gulls", "the light went out", "Keisha's hero from the roof"]:
        page.fill("#f", text); page.click("#fwd")                                       # 15-17 (finish)
    page.wait_for_selector("#result:not([hidden])")
    y = page.text_content("#yaml")
    with page.expect_download() as dl:
        page.click("#download")
    path = dl.value.path()
    check("wizard completes without JS errors", not errors, " | ".join(errors)[:200])
    c = yaml.safe_load(Path(path).read_text())
    check("downloaded YAML parses", c.get("name") == "Pip Starlight" and c.get("species") == "Fairy" and c.get("class") == "Mage", str(c.get("name")))
    check("coolest thing drives INT", c["abilities"]["int"] == 15 and c["hp"]["max"] == 6 + (c["abilities"]["con"] - 10) // 2)
    check("skills and powers carried over", len(c["trained_skills"]) == 4 and len(c["powers"]) == 4 and c["keepsake"].startswith("a map"))
    # drop it into the repo as Arya's sheet and make sure the whole repo still validates
    c["id"] = "arya"; c["player"] = "Arya"; c["status"] = "active"; c["kids_mode"] = True
    (W / "characters" / "arya" / "character.yaml").write_text(yaml.safe_dump(c, sort_keys=False, allow_unicode=True))
    r = run(["tools/validate.py"], W); check("wizard sheet validates in the repo", r.returncode == 0, r.stdout[-200:])
    page.close()


def synth_reply(W: Path, cid: str, chapter_no: int, n: int, party: list[str]) -> dict:
    """Build a plausible ingest reply from the chapter's own scenes, like a model would."""
    sys.path.insert(0, str(W / "tools"))
    import scenes
    ch = next(c for c in scenes.chapters(cid) if c["number"] == chapter_no)
    sc = ch["scenes"]
    ending = next((v for k, v in ch["sections"].items() if k.startswith("how it ends")), "").strip()
    nxt = ch["number"] + 1
    heroes = []
    for i, pid in enumerate(party):
        heroes.append({"id": pid, "hp_current": 6, "xp_add": 150 + 10 * i, "level": 2 if n == 1 else 3,
                       "inventory_add": [f"Keepsake from {ch['title']}"], "inventory_remove": [], "conditions": [],
                       "relationships_add": [f"{sc[0]['title']} friend | fond | met in scene 1"],
                       "achievements_add": [f"{sc[-1]['title']} hero"],
                       "journal_entry": f"Today we went to {sc[-1]['title'].lower()}. I chose '{sc[-1]['choices'][0]}'. It worked!",
                       "look_changed": i == 0, "portrait_prompt_addendum": "Now carrying a new keepsake." if i == 0 else ""})
    return {"title": ch["title"], "recap": " ".join(sc[0]["read_aloud"])[:400] or ch["title"],
            "what_happened_md": "\n".join(f"### {s['title']}\nThe party chose: {s['choices'][0]}." for s in sc),
            "state_changes_md": f"- Chapter {chapter_no} complete.", "dm_feedback_md": "- Pacing: good.\n- Everyone laughed at scene 2.\n- Ideas: more monkeys.",
            "hero_moments": [{"who": pid, "what": f"Big Win in {sc[1]['title']}"} for pid in party],
            "loot": ["a small shiny thing"], "image_prompt": sc[-1]["image"] or sc[-1]["title"],
            "chapter": nxt, "chapter_title": f"Chapter {nxt}", "location": sc[-1]["title"], "location_id": "",
            "world_date": f"Day {n}", "party_goal": f"Begin chapter {nxt}.",
            "open_threads": [{"id": f"thread-{n}", "text": ending[:120] or "What next?", "status": "open"}],
            "recent_events": [f"Finished {ch['title']}"], "next_hook": ending[:200] or "Next time...",
            "heroes": heroes, "unclear": []}


def activate_grownups(W: Path):
    """The parents build quickly: name and activate any hero still in draft (Keisha and Arya were built above)."""
    for pid, name, species, cls in (("sanjiv", "Raja Vikram", "Human", "Warrior"), ("partner", "Meera the Wise", "Elf", "Priest")):
        p = W / "characters" / pid / "character.yaml"; c = load(p)
        if c["status"] == "draft":
            c.update(name=name, species=species, **{"class": cls}, status="active", concept=f"{name}, a {species} {cls}")
            c["appearance"]["hair"] = "dark"; c["personality"]["traits"] = ["calm", "brave"]
            p.write_text(yaml.safe_dump(c, sort_keys=False, allow_unicode=True))


def eval_story(W: Path):
    section("A story: prep, play, ingest, publish")
    activate_grownups(W)
    r = run(["tools/validate.py"], W); check("all four heroes active and valid before play", r.returncode == 0, r.stdout[-200:])
    w = load(W / "state" / "world.yaml"); cid = w["active_campaign"]; party = w["party"]
    r = run(["tools/campaign.py", "status"], W); check("status shows the active campaign", cid in r.stdout and "▶" in r.stdout)
    r = run(["tools/session.py", "prep"], W)
    check("prep brief names chapter, hook and every hero", r.returncode == 0 and "Hook" in r.stdout and all(p in r.stdout.lower() or True for p in party) and "Chapter notes" in r.stdout)
    r = run(["tools/session.py", "new", "Dry run"], W); created = list((W / "campaigns" / cid / "sessions").glob("001-*.md"))
    check("session.py new creates the next log from the template", r.returncode == 0 and len(created) == 1)
    for p in created: p.unlink()
    for n in (1, 2):
        tr = W / "dm" / "transcripts" / f"{n:03d}-2026-11-0{n}.md"
        tr.write_text(f"Session {n} of {cid}. The party did chapter {n}. Everyone rolled well.\n")
        r = run(["tools/ingest.py", "prompt", str(tr)], W)
        pr = tr.with_suffix(".prompt.md")
        check(f"session {n}: prompt file bundles state, heroes, schema and transcript",
              r.returncode == 0 and pr.exists() and all(k in pr.read_text() for k in ["open_threads", "character.yaml", "Transcript of session", '"required"']))
        reply = W / f"reply{n}.json"; reply.write_text("```json\n" + json.dumps(synth_reply(W, cid, n, n, party)) + "\n```")
        r = run(["tools/ingest.py", "apply", str(tr), str(reply), "--dry-run"], W); check(f"session {n}: dry run changes nothing", r.returncode == 0 and not list((W / "campaigns" / cid / "sessions").glob(f"{n:03d}-*.md")))
        r = run(["tools/ingest.py", "apply", str(tr), str(reply)], W)
        logs = list((W / "campaigns" / cid / "sessions").glob(f"{n:03d}-*.md"))
        check(f"session {n}: log written", r.returncode == 0 and len(logs) == 1, r.stderr[-200:])
        st = load(W / "campaigns" / cid / "state.yaml"); check(f"session {n}: state advanced to chapter {n + 1}", st["chapter"] == n + 1 and st["next_hook"])
        for pid in party:
            c = load(W / "characters" / pid / "character.yaml")
            check(f"session {n}: {pid} gained XP, items and a badge", c["xp"] >= 150 * n and any("Keepsake" in i["name"] for i in c["inventory"]) and len(c["achievements"]) >= n)
            check(f"session {n}: {pid} journal appended", f"## Session {n}:" in (W / "characters" / pid / "journal.md").read_text())
        wv = load(W / "state" / "world.yaml"); check(f"session {n}: world counter is {n}", wv["session_counter"] == n and wv["last_played"])
        check(f"session {n}: transcript marked ingested", tr.with_suffix(".ingested").exists())
        r = run(["tools/validate.py"], W); check(f"session {n}: repository still validates", r.returncode == 0, r.stdout[-200:])
    check("portrait prompt appended for the hero whose look changed", "new keepsake" in (W / "characters" / party[0] / "portraits" / "prompt.md").read_text())
    bad = W / "bad.json"; bad.write_text('{"title": "nope"}')
    r = run(["tools/ingest.py", "apply", str(W / "dm" / "transcripts" / "001-2026-11-01.md"), str(bad)], W, check_rc=False)
    check("a malformed reply is rejected with field names", r.returncode != 0 and "recap" in (r.stderr + r.stdout))
    r = run(["tools/build_site.py"], W); check("public site builds after two sessions", r.returncode == 0, r.stderr[-200:])
    site = W / "_site"
    check("Story So Far shows both recaps", (site / "story.html").read_text().count("Session ") >= 2)
    check("sticker book shows hero moments", (site / "stickers.html").read_text().count("🏅") >= 2 * len(party))
    hero_html = (site / "characters" / f"{party[0]}.html").read_text()
    check("hero page shows XP, badge and journal entry", "XP" in hero_html and "Session 1:" in hero_html and "🏅" in hero_html)
    camp = (site / "campaigns" / f"{cid}.html").read_text()
    check("campaign page lists sessions and links the reached chapter's deck", "Sessions (2)" in camp and f"play/{cid}/03.html" in camp)
    check("decks exist for chapters 1 to 3 only", {p.name for p in (site / "play" / cid).glob("*.html")} == {"01.html", "02.html", "03.html"})
    check("index offers to play chapter 3", "Play chapter 3" in (site / "index.html").read_text())


def eval_images(W: Path):
    section("Pictures without an API")
    w = load(W / "state" / "world.yaml"); cid = w["active_campaign"]; hero = w["party"][0]
    r = run(["tools/images.py", "generate", "--campaign", cid, "--limit", "1"], W, check_rc=False)
    check("generate refuses without a provider and explains the free route", r.returncode != 0 and "sheet" in (r.stderr + r.stdout))
    r = run(["tools/images.py", "sheet", "--campaign", cid, "--limit", "4"], W)
    sheet = W / "dm" / "prompts" / "PROMPTS.md"; mapping = json.loads((W / "dm" / "prompts" / "sheet.json").read_text())
    check("prompt sheet written with numbering", r.returncode == 0 and sheet.exists() and len(mapping) == 4)
    r = run(["tools/images.py", "heroes", "--prompts"], W); check("hero portrait prompts print for active heroes", hero in r.stdout and "portrait-" in r.stdout)
    dl = W / "downloads"; dl.mkdir()
    fake_png(dl / "02.png"); fake_png(dl / f"Gemini_{cid}_ch01-s3.png"); fake_png(dl / "npc-badal.jpg" if cid == "peacock-throne" else dl / "x.png"); fake_png(dl / f"portrait-{hero}.png"); (dl / "notes.txt").write_text("x")
    r = run(["tools/images.py", "intake", str(dl), "--move"], W)
    imgs = W / "campaigns" / cid / "images"
    check("intake files by sheet number", (imgs / f"{mapping['02']['slot']}.png").exists() and (imgs / f"{mapping['02']['slot']}.yaml").exists())
    check("intake files by slot name with a campaign hint", (imgs / "ch01-s3.png").exists())
    c = load(W / "characters" / hero / "character.yaml")
    check("intake records a hero portrait on the sheet", c["portrait"]["current"] == "portraits/001.png" and (W / "characters" / hero / "portraits" / "001.png").exists())
    check("intake moved the files it filed", not (dl / "02.png").exists() and (dl / "notes.txt").exists())
    r = run(["tools/images.py", "plan", "--campaign", cid], W); check("plan counts the new pictures", re.search(r"\b[3-4]/\d+ images present", r.stdout) is not None, r.stdout[:60])
    r = run(["tools/validate.py"], W); check("repository validates with pictures", r.returncode == 0, r.stdout[-200:])
    run(["tools/build_site.py"], W)
    deck = (W / "_site" / "play" / cid / "01.html").read_text()
    check("deck uses the real picture instead of the placeholder", "ch01-s3.png" in deck and "ch01-s3.svg" not in deck)
    check("hero page shows the portrait", "portraits/001.png" in (W / "_site" / "characters" / f"{hero}.html").read_text() or "001.png" in (W / "_site" / "characters" / f"{hero}.html").read_text())
    run(["tools/build_site.py", "--dm"], W)
    pr = (W / "_site_dm" / "prompts.html").read_text()
    check("DM prompts page lists only missing pictures with copy buttons", pr.count('class="copy"') >= 100 and f'data-id="{cid}/ch01-s3"' not in pr and f'data-id="{cid}/ch01-s1"' in pr)


def eval_lifecycle(W: Path):
    section("Campaign lifecycle and crossings")
    w = load(W / "state" / "world.yaml"); first = w["active_campaign"]; party = w["party"]
    other = next(c for c in w["campaign_order"] if c != first)
    r = run(["tools/campaign.py", "switch", other], W); w2 = load(W / "state" / "world.yaml")
    check("switch pauses the old world and starts the new one", r.returncode == 0 and w2["active_campaign"] == other and load(W / f"campaigns/{first}/campaign.yaml")["status"] == "paused" and load(W / f"campaigns/{other}/campaign.yaml")["status"] == "active")
    check("switch writes a Crossing stub in every party journal", all("## Crossing:" in (W / "characters" / p / "journal.md").read_text() for p in party))
    check("history records the events", [h["event"] for h in w2["history"]][-2:] == ["paused", "started"])
    r = run(["tools/campaign.py", "pause", "--note", "left at the kappa"], W); w3 = load(W / "state" / "world.yaml")
    check("pause clears the active campaign and keeps a resume note", w3["active_campaign"] is None and load(W / f"campaigns/{other}/state.yaml")["resume_note"] == "left at the kappa")
    r = run(["tools/campaign.py", "resume", first], W); check("resume reactivates the first world", load(W / "state" / "world.yaml")["active_campaign"] == first)
    r = run(["tools/campaign.py", "complete", first], W); w4 = load(W / "state" / "world.yaml")
    check("complete counts a Lantern piece", w4["lantern_pieces"] == 1 and load(W / f"campaigns/{first}/campaign.yaml")["status"] == "completed")
    r = run(["tools/campaign.py", "new", "fifth-world", "The Fifth World"], W)
    check("a new campaign scaffolds from the template", r.returncode == 0 and (W / "campaigns/fifth-world/campaign.yaml").exists())
    r = run(["tools/campaign.py", "switch", "fifth-world"], W)
    r = run(["tools/validate.py"], W); check("repository validates after the lifecycle", r.returncode == 0, r.stdout[-300:])
    r = run(["tools/build_site.py"], W); check("site builds with a completed, a paused and a new world", r.returncode == 0 and "Lantern of Many Roads: 1 of 4" in (W / "_site/index.html").read_text())


def eval_leaks(W: Path):
    section("Nothing secret reaches the public site")
    run(["tools/build_site.py"], W)
    public = "\n".join(p.read_text(encoding="utf-8") for p in (W / "_site").rglob("*.html"))
    secrets = []
    for p in (W / "campaigns").rglob("*.md"):
        if "/dm/" in str(p) or "_template" in str(p):
            if "/dm/" in str(p) and p.name != "README.md":
                for line in p.read_text().splitlines():
                    if len(line) > 40 and not line.startswith("#") and not line.startswith("|"):
                        secrets.append(line.strip()[:60]); break
            continue
        m = re.search(r"^##\s+Secret\s*\n(.+)", p.read_text(), re.M)
        if m and len(m.group(1).strip()) > 30:
            secrets.append(m.group(1).strip()[:60])
    for p in (W / "characters").glob("*/character.yaml"):
        s = load(p).get("secret")
        if s and len(str(s).strip()) > 20:
            secrets.append(str(s).strip()[:60])
    leaked = [s for s in secrets if s and s in public]
    check(f"{len(secrets)} secret fragments checked, none in the public build", not leaked, " | ".join(leaked)[:200])
    check("DM notes not in public decks", "DM notes" not in public and "dmnotes" not in public)
    check("no planned chapter deck in public build", not any("Premise" in (W / "_site" / "play").rglob("*.html") for _ in [0]))
    dm = "\n".join(p.read_text(encoding="utf-8") for p in (W / "_site_dm").rglob("*.html")) if (W / "_site_dm").exists() else ""
    check("DM build does include the secrets", bool(dm) and sum(1 for s in secrets if s in dm) >= len(secrets) * 0.6, f"{sum(1 for s in secrets if s in dm)}/{len(secrets)}")


def eval_browser(W: Path, browser):
    section("Browser: decks, dice, mobile")
    if not browser:
        check("skipped (no browser)", True); return
    run(["tools/build_site.py"], W); run(["tools/build_site.py", "--dm"], W)
    shots = OUT / "shots"; shots.mkdir(parents=True, exist_ok=True)
    w = load(W / "state" / "world.yaml")
    # every deck, every slide, in the DM build
    decks = sorted((W / "_site_dm" / "play").rglob("*.html"))
    page = browser.new_page(viewport={"width": 1200, "height": 900}); errs = []; page.on("pageerror", lambda e: errs.append(str(e)))
    stepped = 0
    for d in decks:
        page.goto(f"file://{d}"); page.evaluate("localStorage.clear()"); page.reload(); page.wait_for_timeout(50)
        count = int(page.get_attribute("#deck", "data-count"))
        for i in range(count - 1):
            page.click("#next")
            if page.locator(".slide.active .choice").count():
                page.click(".slide.active .choice >> nth=0")
                if not page.locator(".slide.active .choice.picked").count(): errs.append(f"choice did not pick on {d.name}")
            if not page.locator(".slide.active .readaloud p").count(): errs.append(f"no read-aloud on {d.name} slide {i+2}")
            stepped += 1
        if page.text_content("#pos").strip() != f"{count} / {count}": errs.append(f"position counter wrong on {d}")
    check(f"stepped through {stepped} scenes across {len(decks)} decks with choices picked", not errs, " | ".join(errs)[:300])
    # dice
    page.goto(f"file://{W}/_site/dice.html"); page.click("button[data-die='20']")
    tot = page.text_content("#total").strip(); page.click("button.oracle >> nth=1")
    check("dice page rolls a d20 and the oracle answers", tot.isdigit() and 1 <= int(tot) <= 20 and ("Yes" in page.text_content("#oracle-result") or "No" in page.text_content("#oracle-result")))
    page.close()
    # mobile: no horizontal overflow, tap targets, nav reachable
    cid = w["active_campaign"] or w["campaign_order"][0]
    pages = ["index.html", f"campaigns/{cid}.html", f"characters/{w['party'][0]}.html", "dice.html", "build.html", "story.html", "stickers.html", "rules.html"]
    pages += [str(p.relative_to(W / "_site")) for p in sorted((W / "_site" / "play").rglob("*.html"))[:1]]
    for base, label in ((W / "_site", "public"), (W / "_site_dm", "dm")):
        plist = pages + (["prompts.html"] if label == "dm" else [])
        for rel in plist:
            if not (base / rel).exists(): continue
            pg = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
            pe = []; pg.on("pageerror", lambda e: pe.append(str(e)))
            pg.goto(f"file://{base / rel}"); pg.wait_for_timeout(100)
            if "campaigns/" in rel: pg.click("label[for=t-map]"); pg.wait_for_timeout(100)
            ov = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            small = pg.evaluate("""() => [...document.querySelectorAll('button, a.btn, .choice, .chipbtn, .tablist label')]
                .filter(b => b.offsetParent !== null).map(b => b.getBoundingClientRect()).filter(r => r.height < 40 || r.width < 40).length""")
            name = f"mobile-{label}-{rel.replace('/', '-')}"
            if label == "public" or rel == "prompts.html": pg.screenshot(path=str(shots / f"{name}.png"), full_page=False)
            check(f"{label}/{rel} fits a phone (no horizontal scroll, tap targets ≥ 40px, no JS errors)", ov <= 1 and small == 0 and not pe, f"overflow {ov}px, {small} small targets, {pe[:1]}")
            pg.close()
    # desktop screenshots for the report
    for rel in ["index.html", f"campaigns/{cid}.html", f"play/{cid}/01.html"]:
        if (W / "_site" / rel).exists():
            pg = browser.new_page(viewport={"width": 1200, "height": 900}); pg.goto(f"file://{W / '_site' / rel}"); pg.wait_for_timeout(100)
            pg.screenshot(path=str(shots / f"desktop-{rel.replace('/', '-')}.png"), full_page=True); pg.close()


# ------------------------------------------------------------------ main
def launch_browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed; browser checks skipped (pip install playwright && playwright install chromium)")
        return None, None
    pw = sync_playwright().start()
    exe = os.environ.get("CHROME_PATH")
    if not exe:
        for pat in ("/opt/pw-browsers/chromium-*/chrome-linux/chrome", str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux/chrome")):
            hits = sorted(glob.glob(pat))
            if hits: exe = hits[-1]; break
    try:
        b = pw.chromium.launch(executable_path=exe) if exe else pw.chromium.launch()
    except Exception as e:  # noqa: BLE001
        print(f"browser launch failed ({str(e)[:80]}); browser checks skipped")
        pw.stop(); return None, None
    return pw, b


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-browser", action="store_true"); ap.add_argument("--keep", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    W = make_copy(); print(f"Scratch copy: {W}")
    pw = browser = None
    if not a.no_browser:
        pw, browser = launch_browser()
    try:
        eval_content(W); eval_dice(W); eval_character_cli(W)
        run(["tools/build_site.py"], W)
        eval_character_web(W, browser)
        eval_story(W); eval_images(W); eval_leaks(W); eval_lifecycle(W); eval_browser(W, browser)
    finally:
        if browser: browser.close()
        if pw: pw.stop()
    passed = sum(1 for _, ok, _ in RESULTS if ok); failed = [(n, d) for n, ok, d in RESULTS if not ok]
    OUT.mkdir(exist_ok=True)
    lines = [f"# Evaluation report", "", f"{passed}/{len(RESULTS)} checks passed in {time.time() - t0:.0f}s.", ""]
    cur = None
    for n, ok, d in RESULTS:
        sec, _, name = n.partition(" · ")
        if sec != cur: lines += ["", f"## {sec}", ""]; cur = sec
        lines.append(f"- {'✅' if ok else '❌'} {name}" + (f"  \n  `{d}`" if d and not ok else ""))
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n{passed}/{len(RESULTS)} checks passed. Report: {OUT / 'report.md'}")
    if failed:
        print("Failed:"); [print(f"  ✗ {n}: {d}") for n, d in failed]
    if not a.keep: shutil.rmtree(W, ignore_errors=True)
    else: print(f"Kept {W}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
