#!/usr/bin/env python3
"""Smoke alarm for machine-flavoured prose. See docs/WRITING.md for the reasoning.

  prose_lint.py                 score every narrative file, print the worst
  prose_lint.py <paths...>      score specific files
  prose_lint.py --strict        exit 1 if any file is above the ceiling

Score = flagged items per 1,000 words. It counts banned vocabulary, "not X but Y" parallels,
triplet lists, "like a X that", trailing -ing clauses, "something <adj>" vagueness, em dashes
in read-aloud lines, and "in a voice like". Only read-aloud blockquotes, NPC/location prose,
overviews and journals are scored; DM notes and YAML are not.
"""
from __future__ import annotations
import argparse
import re, signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CEILING = 6.0          # flags per 1,000 words; the first drafts scored 12 to 20

WORDS = ["tapestry", "testament", "delve", "vibrant", "bustling", "nestled", "in the heart of", "symphony of",
         "whispers of", "echoes of", "canvas", "unleash", "elevate", "intricate", "enchanting", "breathtaking",
         "mesmeri[sz]ing", "timeless", "ethereal", "palpable", "myriad", "plethora", "beacon", "a world of",
         "a sense of", "the very ", "shimmering", "glistening", "realm", "weav(?:e|ing) ", "embrac(?:e|ing) ",
         "canyon of colou?r", "second sky", "like old lamps", "holds its breath", "held its breath",
         "the size of a (?:house|city|town|mountain|palace|cathedral|castle)", "bigger than the (?:town|city|hall|palace)", "somewhere, something", "something (?:enormous|ancient|old|huge|vast)",
         "in a voice like", "like a .{3,40} that (?:decided|has learned|had learned)", "all at once",
         "and it is (?:lovely|beautiful|wonderful)", "exactly symmetrical"]
NEG_PARALLEL = re.compile(r"\bnot (?:just |only |merely )?[^.;,]{2,40}, (?:but|it is|it's)\b", re.I)
# Three parallel words joined "a, b and c". Only fires on three lowercase words whose last is not a
# function word, so "pigeons, drips, and your hat" or "Wren, Teddy, and the Tower" are not caught.
TRIPLET = re.compile(r"\b([a-z]+), ([a-z]+)(?:,)? and (?!(?:the|a|an|from|your|you|it|its|this|that|then|there|anyone|everyone|at|in|on|to|of|with|for|he|she|they|we|his|her|their|our|one|some|all|no|not|nobody|nothing|never|once|now|so)\b)([a-z]+)\b")
TRAILING_ING = re.compile(r", (?:highlighting|underscoring|emphasi[sz]ing|reflecting|symboli[sz]ing|showcasing|creating|making|leaving)\b[^.]*\.", re.I)
EMDASH = re.compile(r"—")

SKIP_LABELS = ("- **Setup:**", "- **Rolls:**", "- **Outcomes:**", "- **Action:**", "- **Image:**", "- **Music:**",
               "- **Jobs for the kids:**", "- **Choices:**", "  - ", "## Secret")


def narrative_lines(path: Path) -> list[tuple[int, str]]:
    """Lines that are player-facing prose."""
    text = path.read_text(encoding="utf-8")
    in_fm = False; out = []
    chapter = "/chapters/" in str(path)
    for i, line in enumerate(text.splitlines(), 1):
        if i == 1 and line.strip() == "---":
            in_fm = True; continue
        if in_fm:
            if line.strip() == "---": in_fm = False
            continue
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("|") or s.startswith("```"):
            continue
        if chapter:
            if s.startswith(">"):
                out.append((i, s.lstrip("> ").strip()))
            continue
        if any(s.startswith(l.strip()) for l in SKIP_LABELS):
            continue
        out.append((i, s))
    return out


def score(path: Path):
    lines = narrative_lines(path)
    words = sum(len(l.split()) for _, l in lines)
    flags = []
    for n, l in lines:
        low = l.lower()
        for w in WORDS:
            for m in re.finditer(w, low):
                flags.append((n, f"word: {m.group(0).strip()}"))
        for m in NEG_PARALLEL.finditer(l):
            flags.append((n, f"not-X-but-Y: {m.group(0)[:40]}"))
        for m in TRIPLET.finditer(l):
            flags.append((n, f"triplet: {m.group(0)}"))
        for m in TRAILING_ING.finditer(l):
            flags.append((n, f"trailing -ing: {m.group(0)[:40]}"))
        if EMDASH.search(l):
            flags.append((n, "em dash in read-aloud"))
    per_k = (len(flags) / words * 1000) if words else 0.0
    return words, flags, per_k


def targets(paths):
    if paths:
        out = []
        for p in paths:
            p = Path(p).resolve(); out += [x for x in p.rglob("*.md")] if p.is_dir() else [p]
        return out
    files = []
    for cid in (ROOT / "campaigns").iterdir():
        if not cid.is_dir() or cid.name.startswith("_"): continue
        for sub in ("chapters", "npcs", "locations"):
            files += [p for p in (cid / sub).glob("*.md") if not p.name.startswith("_")]
        if (cid / "overview.md").exists(): files.append(cid / "overview.md")
        if (cid / "world.md").exists(): files.append(cid / "world.md")
    files += [p for p in (ROOT / "characters").glob("*/journal.md")]
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*"); ap.add_argument("--strict", action="store_true"); ap.add_argument("--show", type=int, default=12)
    a = ap.parse_args(argv)
    rows = []
    for p in targets(a.paths):
        w, f, k = score(p)
        if w: rows.append((k, w, f, p))
    rows.sort(reverse=True)
    tw = sum(r[1] for r in rows); tf = sum(len(r[2]) for r in rows)
    print(f"{len(rows)} files, {tw} narrative words, {tf} flags, {tf / tw * 1000 if tw else 0:.1f} per 1,000 words (ceiling {CEILING})\n")
    for k, w, f, p in rows[: a.show]:
        mark = "✗" if k > CEILING else "·"
        print(f" {mark} {k:5.1f}  {w:5d}w  {p.relative_to(ROOT)}")
        for n, why in f[:4]:
            print(f"         L{n}: {why}")
    over = [r for r in rows if r[0] > CEILING]
    if a.strict and over:
        print(f"\n{len(over)} file(s) above the ceiling."); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
