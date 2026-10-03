#!/usr/bin/env python3
"""Optional: call an image API with the hero's prompt and save the result.

Provider is chosen by IMAGE_PROVIDER (default "openai"). Requires an API key in the environment:
  OPENAI_API_KEY   for provider openai (model gpt-image-1)
This file is deliberately small; swap the provider function for any service you prefer.

  python tools/portrait_generate.py arya --session 1 --note "first portrait"
"""
from __future__ import annotations
import argparse
import base64
import json
import os
import sys
import urllib.request
from datetime import date
from common import CHARACTERS, load_character
from portrait_prompt import compose, main as record_main


def openai_image(prompt: str) -> bytes:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY is not set")
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=json.dumps({"model": "gpt-image-1", "prompt": prompt, "size": "1024x1024", "n": 1}).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.load(r)
    return base64.b64decode(data["data"][0]["b64_json"])


PROVIDERS = {"openai": openai_image}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("id")
    ap.add_argument("--session", type=int, default=0)
    ap.add_argument("--note", default="")
    a = ap.parse_args(argv)
    provider = PROVIDERS[os.environ.get("IMAGE_PROVIDER", "openai")]
    h = load_character(a.id)
    prompt = compose(h)
    png = provider(prompt)
    pdir = CHARACTERS / a.id / "portraits"
    n = len(list(pdir.glob("*.png"))) + 1
    out = pdir / f"{n:03d}.png"
    out.write_bytes(png)
    with open(pdir / "prompt.md", "a", encoding="utf-8") as f:
        f.write(f"\n\n## {date.today()} · {out.name}{' · ' + a.note if a.note else ''}\n\n{prompt}\n")
    print(f"Saved {out}")
    return record_main([a.id, "--record", out.name, "--session", str(a.session), "--note", a.note])


if __name__ == "__main__":
    sys.exit(main())
