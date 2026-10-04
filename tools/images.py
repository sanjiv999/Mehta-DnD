#!/usr/bin/env python3
"""Image pipeline: list every illustration the game can have, compose prompts, generate the
missing ones with a provider of your choice, and record what was made.

  images.py plan [--campaign id] [--missing] [--json]      what exists, what is missing, the prompts
  images.py prompt <campaign> <slot>                       print one composed prompt (paste anywhere)
  images.py generate [--campaign id] [--limit N] [--slots a,b] [--provider openai|stability|cmd] [--dry-run]
  images.py record <campaign> <slot> <file>                register a hand-made or externally made image
  images.py heroes [--limit N]                             portraits for heroes that have none

Providers (choose with --provider or IMAGE_PROVIDER):
  openai     OPENAI_API_KEY, model gpt-image-1
  stability  STABILITY_API_KEY, Stable Image Core
  cmd        IMAGE_CMD, a shell template with {prompt} and {out}, e.g. a local ComfyUI/SD script

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

import yaml
from common import CAMPAIGNS, CHARACTERS, campaign_ids, load_campaign, load_yaml, dump_yaml, character_ids, load_character
from scenes import image_slots, compose_prompt


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


def cmd_generate(a):
    provider = a.provider or os.environ.get("IMAGE_PROVIDER", "openai")
    fn = PROVIDERS[provider]
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


def cmd_heroes(a):
    from portrait_prompt import compose, main as record
    provider = a.provider or os.environ.get("IMAGE_PROVIDER", "openai")
    fn = PROVIDERS[provider]
    done = 0
    for hid in character_ids():
        h = load_character(hid)
        if h.get("portrait", {}).get("current") or h.get("status") == "draft":
            continue
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("--campaign"); p.add_argument("--missing", action="store_true"); p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("prompt"); p.add_argument("campaign"); p.add_argument("slot"); p.set_defaults(fn=cmd_prompt)
    p = sub.add_parser("generate"); p.add_argument("--campaign"); p.add_argument("--limit", type=int, default=0); p.add_argument("--slots"); p.add_argument("--provider"); p.add_argument("--dry-run", action="store_true"); p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_generate)
    p = sub.add_parser("record"); p.add_argument("campaign"); p.add_argument("slot"); p.add_argument("file"); p.add_argument("--note", default=""); p.set_defaults(fn=cmd_record)
    p = sub.add_parser("heroes"); p.add_argument("--limit", type=int, default=0); p.add_argument("--provider"); p.add_argument("--dry-run", action="store_true"); p.set_defaults(fn=cmd_heroes)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
