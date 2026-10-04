"""Parse chapter Markdown into structured scenes, and enumerate image slots.

Chapter convention (see campaigns/_template/chapters/01-template.md):
  ### Scene N: Title (kind)
  > read-aloud lines (player-safe)
  - **Jobs for the kids:** ...        (player-safe, shown as "Your missions")
  - **Choices:**                       (player-safe, shown as buttons)
    - 🐘 Choice text
  - **Image:** one-line art direction  (feeds the image pipeline)
  - **Music:** mood words              (player-safe chip)
  everything else                      (DM-only)
"""
from __future__ import annotations
import re
from pathlib import Path
from common import load_md, CAMPAIGNS

SCENE_RE = re.compile(r"^###\s+Scene\s+(\d+):\s*(.+?)\s*(?:\(([^)]*)\))?\s*$", re.M)
LABEL_RE = re.compile(r"^-\s+\*\*([^*]+?):\*\*\s*(.*)$")
PLAYER_SAFE_LABELS = {"jobs for the kids", "choices", "music"}
HIDDEN_LABELS = {"image"}


def split_sections(body: str) -> dict[str, str]:
    """Top-level '## X' sections of a chapter body."""
    parts = re.split(r"^##\s+(?!#)(.+?)\s*$", body, flags=re.M)
    out = {"_intro": parts[0]}
    for i in range(1, len(parts), 2):
        out[parts[i].strip().lower()] = parts[i + 1]
    return out


def parse_scene_block(number: int, title: str, kind: str, text: str) -> dict:
    read_aloud, jobs, choices, image, music, dm_lines = [], "", [], "", "", []
    lines = text.strip("\n").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith(">"):
            read_aloud.append(line[1:].strip())
            i += 1
            continue
        m = LABEL_RE.match(line)
        if m:
            label, rest = m.group(1).strip().lower(), m.group(2).strip()
            if label == "choices":
                j = i + 1
                while j < len(lines) and re.match(r"^\s+-\s+", lines[j]):
                    choices.append(re.sub(r"^\s+-\s+", "", lines[j]).strip())
                    j += 1
                if rest:
                    choices.extend(c.strip() for c in rest.split("|") if c.strip())
                i = j
                continue
            if label == "jobs for the kids":
                jobs = rest
            elif label == "image":
                image = rest
            elif label == "music":
                music = rest
            else:
                dm_lines.append(line)
            i += 1
            continue
        dm_lines.append(line)
        i += 1
    paragraphs, cur = [], []
    for l in read_aloud:
        if l == "":
            if cur:
                paragraphs.append(" ".join(cur)); cur = []
        else:
            cur.append(l)
    if cur:
        paragraphs.append(" ".join(cur))
    return {
        "number": number, "title": title, "kind": kind or "", "slug": f"s{number}",
        "read_aloud": paragraphs, "jobs": jobs, "choices": choices, "image": image, "music": music,
        "dm_md": "\n".join(dm_lines).strip(),
    }


def parse_chapter(path: Path) -> dict:
    meta, body = load_md(path)
    sections = split_sections(body)
    scenes_text = sections.get("scenes", "")
    scenes = []
    matches = list(SCENE_RE.finditer(scenes_text))
    for idx, m in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(scenes_text)
        scenes.append(parse_scene_block(int(m.group(1)), m.group(2), (m.group(3) or "").strip(),
                                        scenes_text[m.end():end]))
    meta = dict(meta)
    meta["file"] = path.name
    meta["slug"] = path.stem
    meta["scenes"] = scenes
    meta["sections"] = sections
    meta["body"] = body
    meta["dm_md"] = "\n\n".join(
        f"## {k.title()}\n{v.strip()}" for k, v in sections.items()
        if k not in ("_intro", "scenes") and v.strip())
    return meta


def chapters(cid: str) -> list[dict]:
    d = CAMPAIGNS / cid / "chapters"
    out = [parse_chapter(p) for p in sorted(d.glob("*.md")) if not p.name.startswith("_")]
    return sorted(out, key=lambda c: c.get("number", 0))


IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".svg")


def find_image(cid: str, slot: str) -> Path | None:
    """Player art (art/) wins over generated art (images/)."""
    base = CAMPAIGNS / cid
    for folder in ("art", "images"):
        for ext in IMAGE_EXTS:
            p = base / folder / f"{slot}{ext}"
            if p.exists():
                return p
    return None


def image_slots(cid: str, campaign: dict) -> list[dict]:
    """Every image the campaign can have, with its prompt and current file."""
    slots = []
    style = (campaign.get("art_style") or "").strip()

    def add(slot, kind, title, prompt, chapter=None, scene=None):
        slots.append({"slot": slot, "kind": kind, "title": title, "prompt": (prompt or "").strip(),
                      "style": style, "chapter": chapter, "scene": scene,
                      "file": find_image(cid, slot)})

    add("cover", "cover", campaign.get("title", cid), campaign.get("cover_prompt") or campaign.get("tagline"))
    add("map", "map", f"Map of {campaign.get('title', cid)}",
        (campaign.get("map") or {}).get("prompt") or f"An illustrated storybook map of {campaign.get('setting','')}")
    for ch in chapters(cid):
        n = int(ch.get("number", 0))
        add(f"ch{n:02d}", "chapter", ch.get("title", ""), ch.get("image_prompt") or ch.get("summary"), chapter=n)
        for s in ch["scenes"]:
            add(f"ch{n:02d}-{s['slug']}", "scene", f"{ch.get('title','')}: {s['title']}",
                s["image"] or " ".join(s["read_aloud"])[:400], chapter=n, scene=s["number"])
    for sub, kind in (("npcs", "npc"), ("locations", "location")):
        for p in sorted((CAMPAIGNS / cid / sub).glob("*.md")):
            if p.name.startswith("_"):
                continue
            meta, body = load_md(p)
            looks = re.search(r"\*\*(?:Looks|First impression):\*\*\s*(.+)", body)
            add(f"{kind}-{p.stem}", kind, meta.get("name", p.stem),
                meta.get("image_prompt") or (looks.group(1) if looks else meta.get("name", "")))
    return slots


def compose_prompt(slot: dict, overrides: dict | None = None, extra_style: str = "") -> str:
    base = (overrides or {}).get(slot["slot"]) or slot["prompt"]
    kind = slot["kind"]
    frame = {
        "cover": "Wide establishing illustration, no text.",
        "map": "Top-down illustrated fantasy map with painted terrain, no labels or text.",
        "chapter": "Wide cinematic establishing shot, no text.",
        "scene": "Storybook illustration of this moment, wide shot, no text.",
        "npc": "Character portrait, waist-up, centered, clean background with an ornamental border, no text.",
        "location": "Wide establishing illustration of the place, no people in the foreground, no text.",
    }.get(kind, "Illustration, no text.")
    return " ".join(x for x in [base.rstrip(".") + ".", frame, "Style: " + slot["style"], extra_style,
                                "Child-friendly, warm, no gore, no weapons pointed at the viewer, no watermark."] if x)
