#!/usr/bin/env python3
"""Image pipeline: list every illustration the game can have, compose prompts, generate the
missing ones with a provider of your choice, and record what was made.

No API key is needed. The default workflow is copy-and-paste:

  images.py sheet [--campaign id] [--limit N]       write a numbered prompt sheet (PROMPTS.md) to paste into
                                                    Gemini, Claude, or any image app; the DM site build also
                                                    shows it at prompts.html with copy buttons
  images.py intake <folder-or-files...>             file downloaded images: names like ch01-s3.png, npc-badal.jpg,
                                                    portrait-aarya.png, or the sheet number (07.png) all work
  images.py pictures [--show N]                     write PICTURES.md at the repo root: every missing picture,
                                                    most needed first, with the prompt and the number to save as
  images.py intake [folder] [--assign 07,12]        file what landed in inbox/ (default) and refresh PICTURES.md
  images.py plan [--campaign id] [--missing]        what exists, what is missing
  images.py prompt <campaign> <slot>                print one composed prompt
  images.py record <campaign> <slot> <file>         register one image by hand
  images.py heroes --prompts                        print portrait prompts for heroes without one

Optional, only if you ever want an API to do the pasting for you (costs money outside a subscription):
  images.py generate --provider openai|stability|cmd [--campaign id] [--limit N] [--dry-run]
  images.py heroes --provider openai

Human spark: put a better prompt for any slot in campaigns/<id>/images/overrides.yaml, add extra
style notes in campaigns/<id>/images/STYLE.md, or drop the kids' own drawing in campaigns/<id>/art/<slot>.png
(player art always wins over generated art).
"""
from __future__ import annotations
import argparse
import base64
import json
import os
import shlex
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

import re
import yaml
from common import ROOT, world
from common import CAMPAIGNS, CHARACTERS, campaign_ids, load_campaign, load_yaml, dump_yaml, character_ids, load_character, load_md
from scenes import image_slots, compose_prompt, cast_sheet, place_sheet, hero_canon

ROOT_SHEET = ROOT / "dm" / "prompts" / "PROMPTS.md"
PICTURES = ROOT / "PICTURES.md"
NUMBERS = ROOT / "dm" / "prompts" / "sheet.json"      # slot -> stable number, never renumbered
INBOX = ROOT / "inbox"


# ---------------- providers ----------------
def provider_openai(prompt: str, out: Path) -> None:
    key = os.environ.get("OPENAI_API_KEY") or sys.exit("OPENAI_API_KEY is not set")
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=json.dumps({"model": os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1"), "prompt": prompt,
                         "size": os.environ.get("IMAGE_SIZE", "1536x1024"), "n": 1}).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.load(r)
    out.write_bytes(base64.b64decode(data["data"][0]["b64_json"]))


def provider_stability(prompt: str, out: Path) -> None:
    key = os.environ.get("STABILITY_API_KEY") or sys.exit("STABILITY_API_KEY is not set")
    boundary = "----mehta-dnd"
    fields = {"prompt": prompt, "output_format": "png", "aspect_ratio": "16:9"}
    body = b""
    for k, v in fields.items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request("https://api.stability.ai/v2beta/stable-image/generate/core", data=body,
                                 headers={"Authorization": f"Bearer {key}", "Accept": "image/*",
                                          "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=180) as r:
        out.write_bytes(r.read())


def provider_cmd(prompt: str, out: Path) -> None:
    tpl = os.environ.get("IMAGE_CMD") or sys.exit("IMAGE_CMD is not set (template with {prompt} and {out})")
    cmd = tpl.replace("{prompt}", shlex.quote(prompt)).replace("{out}", shlex.quote(str(out)))
    subprocess.run(cmd, shell=True, check=True)


PROVIDERS = {"openai": provider_openai, "stability": provider_stability, "cmd": provider_cmd}


# ---------------- helpers ----------------
def campaign_slots(cid: str):
    c = load_campaign(cid)
    d = CAMPAIGNS / cid / "images"
    overrides = load_yaml(d / "overrides.yaml") if (d / "overrides.yaml").exists() else {}
    extra = ""
    if (d / "STYLE.md").exists():
        extra = " ".join(l.strip() for l in (d / "STYLE.md").read_text(encoding="utf-8").splitlines()
                         if l.strip() and not l.lstrip().startswith(("#", "<!--")))
    slots = image_slots(cid, c)
    cast, places = cast_sheet(cid), place_sheet(cid)
    for s in slots:
        s["final_prompt"] = compose_prompt(s, overrides, extra, cast, places)
        s["campaign"] = cid
        s["sidecar"] = d / f"{s['slot']}.yaml"
        s["aspect"] = "portrait 3:4" if s["kind"] in ("npc", "portrait") else "landscape 16:9"
    return slots


def write_sidecar(slot: dict, out: Path, provider: str, note: str = "") -> None:
    meta = {"slot": slot["slot"], "kind": slot["kind"], "title": slot["title"], "file": out.name,
            "prompt": slot["final_prompt"], "provider": provider, "date": str(date.today()), "note": note}
    dump_yaml(slot["sidecar"], meta)


# ---------------- commands ----------------
def cmd_plan(a):
    import signal
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    cids = [a.campaign] if a.campaign else campaign_ids()
    rows = []
    for cid in cids:
        for s in campaign_slots(cid):
            if a.missing and s["file"]:
                continue
            rows.append(s)
    if a.json:
        print(json.dumps([{k: (str(v) if isinstance(v, Path) else v) for k, v in s.items()} for s in rows], indent=2))
        return 0
    total = sum(len(campaign_slots(c)) for c in cids)
    have = sum(1 for c in cids for s in campaign_slots(c) if s["file"])
    print(f"{have}/{total} images present across {', '.join(cids)}\n")
    cur = None
    for s in rows:
        if s["campaign"] != cur:
            cur = s["campaign"]; print(f"== {cur} ==")
        mark = "✓" if s["file"] else "·"
        print(f" {mark} {s['slot']:18} {s['kind']:9} {s['title'][:60]}")
    print("\nNext: python tools/images.py generate --campaign <id> --limit 5 --provider openai")
    return 0


def cmd_prompt(a):
    for s in campaign_slots(a.campaign):
        if s["slot"] == a.slot:
            print(s["final_prompt"]); return 0
    sys.exit(f"No slot {a.slot!r}; run images.py plan --campaign {a.campaign}")


def need_provider(a):
    provider = a.provider or os.environ.get("IMAGE_PROVIDER")
    if not provider or provider == "manual":
        sys.exit("No API provider chosen. The default workflow needs no key:\n"
                 "  python tools/images.py sheet --campaign <id>     then paste prompts into Gemini/Claude\n"
                 "  python tools/images.py intake ~/Downloads        to file what you downloaded\n"
                 "To use a paid API anyway, pass --provider openai|stability|cmd.")
    return PROVIDERS[provider], provider


def cmd_generate(a):
    fn, provider = need_provider(a)
    cids = [a.campaign] if a.campaign else campaign_ids()
    wanted = set(a.slots.split(",")) if a.slots else None
    done = 0
    order = {"cover": 0, "chapter": 1, "scene": 2, "location": 3, "npc": 4, "map": 5}
    for cid in cids:
        slots = sorted(campaign_slots(cid), key=lambda s: (order.get(s["kind"], 9), s["slot"]))
        for s in slots:
            if wanted and s["slot"] not in wanted:
                continue
            if s["file"] and not a.force:
                continue
            if a.limit and done >= a.limit:
                break
            out = CAMPAIGNS / cid / "images" / f"{s['slot']}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            print(f"[{provider}] {cid}/{s['slot']}: {s['final_prompt'][:90]}...")
            if not a.dry_run:
                fn(s["final_prompt"], out)
                write_sidecar(s, out, provider)
            done += 1
    print(f"{'Would generate' if a.dry_run else 'Generated'} {done} image(s).")
    return 0


def cmd_record(a):
    src = Path(a.file)
    if not src.exists():
        sys.exit(f"{src} not found")
    for s in campaign_slots(a.campaign):
        if s["slot"] == a.slot:
            out = CAMPAIGNS / a.campaign / "images" / f"{a.slot}{src.suffix.lower()}"
            out.parent.mkdir(parents=True, exist_ok=True)
            if src.resolve() != out.resolve():
                out.write_bytes(src.read_bytes())
            write_sidecar(s, out, "manual", a.note)
            print(f"Recorded {out}"); return 0
    sys.exit(f"No slot {a.slot!r}")


def hero_prompts():
    from portrait_prompt import compose
    out = []
    for hid in character_ids():
        h = load_character(hid)
        if h.get("portrait", {}).get("current") or h.get("status") == "draft":
            continue
        out.append({"slot": f"portrait-{hid}", "kind": "portrait", "title": h.get("name") or hid,
                    "final_prompt": compose(h), "campaign": "heroes", "hero": hid, "file": None,
                    "refs": [], "aspect": "portrait 3:4"})
    return out


def cmd_heroes(a):
    from portrait_prompt import main as record
    if a.prompts or not (a.provider or os.environ.get("IMAGE_PROVIDER")):
        hp = hero_prompts()
        if not hp:
            print("Every active hero already has a portrait (draft heroes are skipped)."); return 0
        for s in hp:
            print(f"## {s['slot']}  ({s['title']})\n\n{s['final_prompt']}\n")
        print("Save the pictures as portrait-<id>.png and run: python tools/images.py intake <folder>")
        return 0
    fn, provider = need_provider(a)
    done = 0
    for hid in character_ids():
        h = load_character(hid)
        if h.get("portrait", {}).get("current") or h.get("status") == "draft":
            continue
        from portrait_prompt import compose
        if a.limit and done >= a.limit:
            break
        prompt = compose(h)
        pdir = CHARACTERS / hid / "portraits"
        n = len(list(pdir.glob("*.png"))) + 1
        out = pdir / f"{n:03d}.png"
        print(f"[{provider}] {hid}: {prompt[:90]}...")
        if not a.dry_run:
            fn(prompt, out)
            with open(pdir / "prompt.md", "a", encoding="utf-8") as f:
                f.write(f"\n\n## {date.today()} · {out.name}\n\n{prompt}\n")
            record([hid, "--record", out.name, "--session", "0", "--note", "first portrait"])
        done += 1
    print(f"{'Would generate' if a.dry_run else 'Generated'} {done} portrait(s).")
    return 0


ORDER = {"cover": 0, "chapter": 1, "npc": 2, "location": 3, "scene": 4, "map": 5}


def numbers() -> dict:
    """Stable picture numbers. A slot keeps its number for ever, so '07.png' always means the same picture."""
    data = json.loads(NUMBERS.read_text()) if NUMBERS.exists() else {}
    return data


def assign_numbers(rows: list[dict]) -> dict:
    data = numbers()
    used = {int(k) for k in data}
    nxt = max(used) + 1 if used else 1
    for s in rows:
        key = f"{s['campaign']}/{s['slot']}"
        if not any(v.get("campaign") == s["campaign"] and v.get("slot") == s["slot"] for v in data.values()):
            data[f"{nxt:02d}"] = {"campaign": s["campaign"], "slot": s["slot"]}; nxt += 1
    NUMBERS.parent.mkdir(parents=True, exist_ok=True)
    NUMBERS.write_text(json.dumps(data, indent=2), encoding="utf-8")
    back = {(v["campaign"], v["slot"]): k for k, v in data.items()}
    for s in rows:
        s["number"] = back[(s["campaign"], s["slot"])]
    return data


def chapter_mentions(cid: str, n: int) -> set[str]:
    """Slots for people and places that appear in chapter n's text."""
    from scenes import chapters, cast_sheet, place_sheet, _mentions
    text = ""
    for ch in chapters(cid):
        if int(ch.get("number", 0)) == n:
            text = " ".join(" ".join(s["read_aloud"]) + " " + (s.get("jobs") or "") + " " + s.get("image", "") + " " + (s.get("dm_md") or "") for s in ch["scenes"])
    hits = set()
    for p in sorted((CAMPAIGNS / cid / "npcs").glob("*.md")):
        meta, _ = load_md(p)
        from scenes import _keys
        if _mentions(text, {"keys": _keys(meta.get("name", p.stem))}): hits.add(f"npc-{p.stem}")
    for p in sorted((CAMPAIGNS / cid / "locations").glob("*.md")):
        meta, _ = load_md(p)
        if _mentions(text, {"keys": _keys(meta.get("name", p.stem))}): hits.add(f"loc-{p.stem}")
    return hits


def sheet_rows(cids, limit=0, include_heroes=True):
    """Missing pictures in the order the table needs them: the active world's current chapter first."""
    w = world(); active = w.get("active_campaign")
    rows = []
    for cid in cids:
        slots = [s for s in campaign_slots(cid) if not s["file"]]
        st = load_campaign(cid).get("state") or {}
        cur = int(st.get("chapter") or 1)
        near = chapter_mentions(cid, cur)

        def rank(s):
            k, ch = s["kind"], s.get("chapter")
            if k == "cover": return (0, 0, s["slot"])
            if ch == cur: return (1, 0 if k == "chapter" else 1, s["slot"])
            if s["slot"] in near: return (2, ORDER.get(k, 9), s["slot"])
            if ch and ch > cur: return (3, ch, s["slot"])
            if ch and ch < cur: return (5, ch, s["slot"])
            return (4, ORDER.get(k, 9), s["slot"])
        rows += [dict(s, rank=rank(s)) for s in sorted(slots, key=rank)]
    rows.sort(key=lambda s: (0 if s["campaign"] == active else 1, s["rank"]))
    if include_heroes:
        heroes = hero_prompts()
        rows = rows[:1] + heroes + rows[1:] if rows else heroes
    assign_numbers(rows)
    return rows[:limit] if limit else rows


def cmd_sheet(a):
    cids = [a.campaign] if a.campaign else campaign_ids()
    rows = sheet_rows(cids, a.limit)
    lines = ["# Prompt sheet", "",
             "Paste each prompt into Gemini, Claude, or any image app. Save the picture with the slot name",
             "(for example `ch01-s3.png`) or just the number (`07.png`), then run",
             "`python tools/images.py intake <folder>`. Generated " + str(date.today()) + ".", ""]
    for s in rows:
        lines += [f"## {s['number']} · {s['campaign']} · `{s['slot']}` · {s['title']}", "", s["final_prompt"], ""]
    out = ROOT_SHEET if a.out is None else Path(a.out)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(rows)} prompts written to {out} (numbering saved in sheet.json).")
    print("Tip: python tools/build_site.py --dm gives the same sheet at _site_dm/prompts.html with copy buttons.")
    return 0


def _entry(s: dict) -> list[str]:
    fname = f"{s['number']}.png"
    attach = ""
    if s.get("refs"):
        attach = "Attach first: " + ", ".join(f"`{Path(r).relative_to(ROOT)}` ({n})" for n, r in s["refs"]) + ". "
    where = f"characters/{s['hero']}/portraits/" if s.get("hero") else f"campaigns/{s['campaign']}/images/"
    return [f"### {s['number']} · {s['title']}", "",
            f"Save as **`{fname}`** and upload to `inbox/`. {s['aspect'].capitalize()}. {attach}"
            f"<sub>slot `{s['slot']}` → `{where}`</sub>", "", "```text", s["final_prompt"], "```", ""]


def cmd_pictures(a):
    """Write PICTURES.md at the repo root: every missing picture, most needed first, with the prompt to paste."""
    w = world(); active = w.get("active_campaign")
    rows = sheet_rows(campaign_ids(), 0)
    done = [(cid, s) for cid in campaign_ids() for s in campaign_slots(cid) if s["file"]]
    cur = int((load_campaign(active).get("state") or {}).get("chapter") or 1) if active else 1
    title = load_campaign(active).get("title", active) if active else ""
    L = ["# Pictures to make", "",
         f"Every picture the game is still missing, most needed first. Regenerated {date.today()}: "
         f"{len(done)} done, {len(rows)} to go.", "",
         "**How:** copy a prompt into Gemini (or Claude), attach any reference pictures it names, save the one you like "
         f"as the number shown (`07.png`), and upload it to the `inbox/` folder here on GitHub (Add file → Upload files, "
         "works on a phone). GitHub files it, rebuilds the site and crosses it off this list. Or paste it in the chat "
         "and say the number.", ""]
    nxt = [s for s in rows if s["campaign"] == active and (s["rank"][0] <= 2 or s.get("hero"))] if active else []
    if nxt:
        L += [f"## Next session: {title}, chapter {cur}", "",
              "These are the ones the kids will see first: the cover, this chapter's scenes, the people and places "
              "in it, and the heroes.", ""]
        for s in nxt: L += _entry(s)
    rest = [s for s in rows if s not in nxt]
    if rest:
        L += ["## Everything else", "", "<details><summary>" + f"{len(rest)} more, in order of need</summary>", ""]
        for s in rest: L += _entry(s)
        L += ["</details>", ""]
    if done:
        L += ["## Done", "", "<details><summary>" + f"{len(done)} pictures in place</summary>", ""]
        L += [f"- `{cid}/{s['slot']}` → `{s['file'].relative_to(ROOT)}`" for cid, s in done] + ["", "</details>", ""]
    PICTURES.write_text("\n".join(L), encoding="utf-8")
    print(f"PICTURES.md: {len(nxt)} for the next session, {len(rest)} more, {len(done)} done.")
    if a.show:
        for s in (nxt or rows)[:a.show]:
            print("\n" + "\n".join(_entry(s)))
    return 0


def place_image(cid: str, slot: str, src: Path, note: str) -> str:
    if slot.startswith("portrait-"):
        from portrait_prompt import main as record
        hid = slot[len("portrait-"):]
        pdir = CHARACTERS / hid / "portraits"
        if not pdir.exists():
            return f"skip {src.name}: no hero {hid}"
        n = len(list(pdir.glob("*.png"))) + len(list(pdir.glob("*.jpg"))) + 1
        dest = pdir / f"{n:03d}{src.suffix.lower()}"
        dest.write_bytes(src.read_bytes())
        record([hid, "--record", dest.name, "--session", "0", "--note", note or "intake"])
        return f"{src.name} -> characters/{hid}/portraits/{dest.name}"
    for s in campaign_slots(cid):
        if s["slot"] == slot:
            dest = CAMPAIGNS / cid / "images" / f"{slot}{src.suffix.lower()}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src.read_bytes())
            write_sidecar(s, dest, "manual", note)
            return f"{src.name} -> campaigns/{cid}/images/{dest.name}"
    return f"skip {src.name}: no slot {slot!r} in {cid}"


def cmd_intake(a):
    sheet = numbers()
    all_slots = {cid: {s["slot"] for s in campaign_slots(cid)} for cid in campaign_ids()}
    files = []
    for p in (a.paths or [str(INBOX)]):
        p = Path(p).expanduser()
        if not p.exists():
            continue
        files += sorted((x for x in p.iterdir() if x.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")),
                        key=lambda x: (x.stat().st_mtime, x.name)) if p.is_dir() else [p]
    if not files:
        print("No image files found."); return 1
    assigned = {}
    if a.assign:
        nums = [n.strip().zfill(2) for n in a.assign.split(",") if n.strip()]
        if len(nums) != len(files):
            sys.exit(f"--assign names {len(nums)} numbers but there are {len(files)} files: {', '.join(f.name for f in files)}")
        assigned = dict(zip((f.name for f in files), nums))
    for f in files:
        stem = f.stem.lower()
        done = None
        m = re.match(r"^(\d{2})\b", assigned.get(f.name, stem))
        if m and m.group(1) in sheet:
            e = sheet[m.group(1)]; done = place_image(e["campaign"], e["slot"], f, f"sheet #{m.group(1)}")
        if not done and stem.startswith("portrait-"):
            done = place_image("", re.sub(r"[ _].*$", "", stem), f, "intake")
        if not done:
            hits = [(cid, s) for cid, slots in all_slots.items() for s in slots if s in stem]
            if hits:
                longest = max(len(s) for _, s in hits)
                hits = [(cid, s) for cid, s in hits if len(s) == longest]
                cids = {cid for cid, _ in hits}
                if len(cids) == 1:
                    cid = hits[0][0]
                elif a.campaign and a.campaign in cids:
                    cid = a.campaign
                elif any(c in stem for c in cids):
                    cid = next(c for c in cids if c in stem)
                else:
                    cid = world().get("active_campaign") if world().get("active_campaign") in cids else sorted(cids)[0]
                    print(f"  ({f.name}: slot {hits[0][1]!r} exists in {', '.join(sorted(cids))}; using {cid}. "
                          f"Put the campaign id in the file name or pass --campaign to choose.)")
                done = place_image(cid, hits[0][1], f, "intake")
        print(done or f"skip {f.name}: name it after a slot (ch01-s3, npc-badal, portrait-aarya) or a picture number (07)")
        if done and not done.startswith("skip") and a.move:
            f.unlink()
    if not a.no_list:
        cmd_pictures(argparse.Namespace(show=0))
    print("Rebuild the site to see them: python tools/build_site.py")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("--campaign"); p.add_argument("--missing", action="store_true"); p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("prompt"); p.add_argument("campaign"); p.add_argument("slot"); p.set_defaults(fn=cmd_prompt)
    p = sub.add_parser("generate"); p.add_argument("--campaign"); p.add_argument("--limit", type=int, default=0); p.add_argument("--slots"); p.add_argument("--provider"); p.add_argument("--dry-run", action="store_true"); p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_generate)
    p = sub.add_parser("record"); p.add_argument("campaign"); p.add_argument("slot"); p.add_argument("file"); p.add_argument("--note", default=""); p.set_defaults(fn=cmd_record)
    p = sub.add_parser("heroes"); p.add_argument("--limit", type=int, default=0); p.add_argument("--provider"); p.add_argument("--dry-run", action="store_true"); p.add_argument("--prompts", action="store_true"); p.set_defaults(fn=cmd_heroes)
    p = sub.add_parser("sheet"); p.add_argument("--campaign"); p.add_argument("--limit", type=int, default=0); p.add_argument("--out"); p.set_defaults(fn=cmd_sheet)
    p = sub.add_parser("pictures"); p.add_argument("--show", type=int, default=0, help="also print the first N entries"); p.set_defaults(fn=cmd_pictures)
    p = sub.add_parser("intake"); p.add_argument("paths", nargs="*", help="folder(s) or files; default: inbox/"); p.add_argument("--assign", help="picture numbers for the files in upload order, e.g. 07,12,13"); p.add_argument("--no-list", action="store_true"); p.add_argument("--campaign", help="campaign for slot names that exist in several worlds (default: the active one)"); p.add_argument("--move", action="store_true", help="delete the source file after filing"); p.set_defaults(fn=cmd_intake)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
