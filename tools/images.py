#!/usr/bin/env python3
"""Image pipeline: list every illustration the game can have, compose prompts, generate the
missing ones with a provider of your choice, and record what was made.

No API key is needed. The default workflow is copy-and-paste:

  images.py sheet [--campaign id] [--limit N]       write a numbered prompt sheet (PROMPTS.md) to paste into
                                                    Gemini, Claude, or any image app; the DM site build also
                                                    shows it at prompts.html with copy buttons
  images.py intake <folder-or-files...>             file downloaded images: names like ch01-s3.png, npc-badal.jpg,
                                                    portrait-arya.png, or the sheet number (07.png) all work
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
from common import CAMPAIGNS, CHARACTERS, campaign_ids, load_campaign, load_yaml, dump_yaml, character_ids, load_character
from scenes import image_slots, compose_prompt

ROOT_SHEET = ROOT / "dm" / "prompts" / "PROMPTS.md"


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
    for s in slots:
        s["final_prompt"] = compose_prompt(s, overrides, extra)
        s["campaign"] = cid
        s["sidecar"] = d / f"{s['slot']}.yaml"
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
                    "final_prompt": compose(h), "campaign": "heroes", "hero": hid, "file": None})
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


def sheet_rows(cids, limit=0, include_heroes=True):
    rows = []
    for cid in cids:
        rows += sorted((s for s in campaign_slots(cid) if not s["file"]), key=lambda s: (ORDER.get(s["kind"], 9), s["slot"]))
    if include_heroes:
        rows += hero_prompts()
    return rows[:limit] if limit else rows


def cmd_sheet(a):
    cids = [a.campaign] if a.campaign else campaign_ids()
    rows = sheet_rows(cids, a.limit)
    mapping = {}
    lines = ["# Prompt sheet", "",
             "Paste each prompt into Gemini, Claude, or any image app. Save the picture with the slot name",
             "(for example `ch01-s3.png`) or just the number (`07.png`), then run",
             "`python tools/images.py intake <folder>`. Generated " + str(date.today()) + ".", ""]
    for i, s in enumerate(rows, 1):
        mapping[f"{i:02d}"] = {"campaign": s["campaign"], "slot": s["slot"]}
        lines += [f"## {i:02d} · {s['campaign']} · `{s['slot']}` · {s['title']}", "", s["final_prompt"], ""]
    out = ROOT_SHEET if a.out is None else Path(a.out)
    out.write_text("\n".join(lines), encoding="utf-8")
    (out.parent / "sheet.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    print(f"{len(rows)} prompts written to {out} (numbering saved in sheet.json).")
    print("Tip: python tools/build_site.py --dm gives the same sheet at _site_dm/prompts.html with copy buttons.")
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
    sheet = {}
    sp = ROOT_SHEET.parent / "sheet.json"
    if sp.exists():
        sheet = json.loads(sp.read_text())
    all_slots = {cid: {s["slot"] for s in campaign_slots(cid)} for cid in campaign_ids()}
    files = []
    for p in a.paths:
        p = Path(p).expanduser()
        files += sorted(x for x in p.iterdir() if x.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")) if p.is_dir() else [p]
    if not files:
        print("No image files found."); return 1
    for f in files:
        stem = f.stem.lower()
        done = None
        m = re.match(r"^(\d{2})\b", stem)
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
        print(done or f"skip {f.name}: name it after a slot (ch01-s3, npc-badal, portrait-arya) or a sheet number (07)")
        if done and not done.startswith("skip") and a.move:
            f.unlink()
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
    p = sub.add_parser("intake"); p.add_argument("paths", nargs="+"); p.add_argument("--campaign", help="campaign for slot names that exist in several worlds (default: the active one)"); p.add_argument("--move", action="store_true", help="delete the source file after filing"); p.set_defaults(fn=cmd_intake)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
