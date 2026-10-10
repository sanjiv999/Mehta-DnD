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

    def add(slot, kind, title, prompt, chapter=None, scene=None, context=None, **extra):
        slots.append({"slot": slot, "kind": kind, "title": title, "prompt": (prompt or "").strip(),
                      "style": style, "chapter": chapter, "scene": scene, "context": context or {},
                      "file": find_image(cid, slot), **extra})

    add("cover", "cover", campaign.get("title", cid), campaign.get("cover_prompt") or campaign.get("tagline"))
    add("map", "map", f"Map of {campaign.get('title', cid)}",
        (campaign.get("map") or {}).get("prompt") or f"An illustrated storybook map of {campaign.get('setting','')}")
    for ch in chapters(cid):
        n = int(ch.get("number", 0))
        add(f"ch{n:02d}", "chapter", ch.get("title", ""), ch.get("image_prompt") or ch.get("summary"), chapter=n)
        for s in ch["scenes"]:
            add(f"ch{n:02d}-{s['slug']}", "scene", f"{ch.get('title','')}: {s['title']}",
                s["image"] or " ".join(s["read_aloud"])[:400], chapter=n, scene=s["number"],
                context={"read_aloud": " ".join(s["read_aloud"]), "jobs": s.get("jobs") or "", "dm": s.get("dm_md") or ""})
    ex = CAMPAIGNS / cid / "images" / "extras.yaml"
    if ex.exists():                      # extra pictures for a scene, such as a fight or its payoff
        from common import load_yaml
        for slot, e in (load_yaml(ex) or {}).items():
            add(slot, "scene", e.get("title", slot), e.get("prompt", ""), chapter=e.get("chapter"),
                scene=e.get("scene"), extra_of=e.get("scene"), dm_only=bool(e.get("dm_only")))
    for sub, kind in (("npcs", "npc"), ("locations", "location")):
        for p in sorted((CAMPAIGNS / cid / sub).glob("*.md")):
            if p.name.startswith("_"):
                continue
            meta, body = load_md(p)
            looks = re.search(r"\*\*(?:Looks|First impression):\*\*\s*(.+)", body)
            prompt = meta.get("image_prompt") or (looks.group(1) if looks else meta.get("name", ""))
            if kind == "npc" and looks and looks.group(1).strip().rstrip(".") not in prompt:
                prompt = prompt.rstrip(".") + ". Canon look: " + looks.group(1).strip()
            g = lambda k: (re.search(r"\*\*" + k + r":\*\*\s*(.+)", body) or [None, ""])[1].strip()
            add(f"{kind}-{p.stem}", kind, meta.get("name", p.stem), prompt, stem=p.stem,
                place={"built": g("Built by"), "hour": g("Hour")} if kind == "location" else None)
    return slots


GENERIC = {"road", "fort", "court", "mirror", "hall", "tower", "ring", "docks", "dock", "springs", "lake", "market",
           "hedge", "peak", "station", "castle", "gate", "whispers", "western", "night", "deep", "halls", "core",
           "garden", "deck", "edge", "heart", "cloud", "ship", "sea", "mountain", "shrine", "bay", "square", "great"}
TITLE_WORDS = {"the", "and", "of", "old", "lady", "lord", "captain", "chair", "dockmaster", "keeper", "mayor",
               "councillor", "hakim", "vizier", "bibi", "rani", "nagini", "padishah", "shahzadi", "thane", "nana",
               "kappa", "okami", "parrot", "child", "whale", "hobby", "club", "and", "a", "an"}
FRAMES = {
    "cover": "Wide establishing illustration for a book cover, landscape 16:9.",
    "map": "Top-down illustrated storybook map with painted terrain, landscape 16:9, no labels.",
    "chapter": "Wide establishing shot that opens a chapter, landscape 16:9.",
    "scene": "Storybook illustration of this exact moment, wide shot, landscape 16:9, the characters mid-action.",
    "npc": "Character portrait, waist-up, centred, looking slightly past the viewer, plain background in the world's palette with a narrow ornamental border, portrait 3:4.",
    "location": "Wide establishing illustration of the place at the stated hour, people small or absent, landscape 16:9.",
    "portrait": "Character portrait, waist-up, centred, looking slightly past the viewer, plain background with a narrow ornamental border, portrait 3:4.",
}
RULES = ("One consistent style across the whole book: same palette, same line, same light. No text, no lettering, "
         "no speech bubbles, no watermark. Child-friendly, warm, no gore, no weapons pointed at the viewer.")


def _keys(name: str) -> list[str]:
    """Words that identify a character or place in prose: 'Shahzadi Zeb' -> ['shahzadi zeb', 'zeb']."""
    name = re.sub(r"\(.*?\)", "", name).strip()
    keys = [name.lower()]
    for w in re.split(r"[\s,]+", name):
        w = w.strip("'\"*").lower()
        if len(w) >= 3 and w not in TITLE_WORDS and w not in GENERIC and not w.endswith("-"):
            keys.append(w)
    return keys


def cast_sheet(cid: str) -> list[dict]:
    """Every recurring face in a world with its canonical look, so prompts describe it the same way every time."""
    out = []
    for p in sorted((CAMPAIGNS / cid / "npcs").glob("*.md")):
        if p.name.startswith("_"):
            continue
        meta, body = load_md(p)
        looks = re.search(r"\*\*(?:Looks|First impression):\*\*\s*(.+)", body)
        if not looks:
            continue
        name = meta.get("name", p.stem)
        out.append({"name": name, "keys": _keys(name), "look": looks.group(1).strip(),
                    "ref": find_image(cid, f"npc-{p.stem}")})
    try:
        from common import character_ids, load_character, CHARACTERS
        for hid in character_ids():
            h = load_character(hid)
            if h.get("status") != "active" or not h.get("name"):
                continue
            cur = (h.get("portrait") or {}).get("current")
            ref = CHARACTERS / hid / cur if cur and (CHARACTERS / hid / cur).exists() else None
            out.append({"name": h["name"], "keys": _keys(h["name"]) + [str(h.get("player", "")).lower(), "heroes", "hero", "party", "children", "child", "kids", "the kids"],
                        "look": hero_canon(h), "ref": ref, "hero": True})
    except Exception:
        pass
    return out


def hero_canon(h: dict) -> str:
    """One sentence that every picture of a hero must agree with. The DM can pin it in portrait.canon."""
    pinned = (h.get("portrait") or {}).get("canon")
    if pinned:
        return pinned.strip()
    ap = h.get("appearance") or {}
    bits = [" ".join(x for x in [ap.get("age"), h.get("species"), h.get("class")] if x)]
    for k in ("height", "build"):
        if ap.get(k): bits.append(ap[k])
    if ap.get("hair"): bits.append(f"{ap['hair']} hair")
    if ap.get("eyes"): bits.append(f"{ap['eyes']} eyes")
    if ap.get("skin"): bits.append(ap["skin"])
    if ap.get("clothing"): bits.append(f"wearing {ap['clothing']}")
    if ap.get("distinguishing"): bits.append(ap["distinguishing"])
    if ap.get("colors"): bits.append(f"colours {ap['colors']}")
    if h.get("keepsake"): bits.append(f"carries {h['keepsake'].rstrip('.')}")
    return ", ".join(b for b in bits if b)


def place_sheet(cid: str) -> list[dict]:
    out = []
    for p in sorted((CAMPAIGNS / cid / "locations").glob("*.md")):
        if p.name.startswith("_"):
            continue
        meta, body = load_md(p)
        g = lambda k: (re.search(r"\*\*" + k + r":\*\*\s*(.+)", body) or [None, ""])[1].strip()
        seen, hour, built = g("First seen"), g("Hour"), g("Built by")
        if not (seen or built):
            continue
        name = meta.get("name", p.stem)
        out.append({"name": name, "keys": _keys(name), "seen": seen, "hour": hour, "built": built,
                    "ref": find_image(cid, f"loc-{p.stem}")})


    return out


def _mentions(text: str, entry: dict) -> bool:
    low = " " + re.sub(r"[^a-z0-9' ]+", " ", re.sub(r"['\u2019]s\b", "", text.lower())) + " "
    return any(f" {k} " in low for k in entry["keys"])


def compose_prompt(slot: dict, overrides: dict | None = None, extra_style: str = "",
                   cast: list[dict] | None = None, places: list[dict] | None = None) -> str:
    """Layered prompt: style anchor, the moment, who is in it (canon looks), where (canon place), framing, rules.

    The same cast and place sentences are reused in every prompt that mentions them, which is what keeps
    a face or a building the same from picture to picture. References to attach are listed in slot["refs"]."""
    base = ((overrides or {}).get(slot["slot"]) or slot["prompt"]).strip().rstrip(".")
    kind = slot["kind"]
    ctx = slot.get("context") or {}
    people_text = " ".join([base, ctx.get("read_aloud", ""), ctx.get("jobs", "")])
    place_text = " ".join([base, ctx.get("read_aloud", "")])
    who, where, refs = [], [], []
    if kind in ("scene", "chapter", "cover", "npc"):
        for c in (cast or []):
            if kind == "npc" and slot["slot"] == f"npc-{slot.get('stem')}":
                continue
            if _mentions(people_text, c) and len(who) < 4:
                who.append(f"{c['name']}: {c['look'].rstrip('.')}.")
                if c.get("ref"): refs.append((c["name"], c["ref"]))
    if kind in ("scene", "chapter", "cover"):
        for pl in (places or []):
            if _mentions(place_text, pl) and len(where) < 1:
                desc = pl["seen"] or pl["built"]
                light = f" Time of day: {pl['hour'].rstrip('.')}." if pl["hour"] and len(pl["hour"].split()) <= 14 else ""
                where.append(f"{pl['name']}: {desc.rstrip('.')}.{light}")
                if pl.get("ref"): refs.append((pl["name"], pl["ref"]))
    if kind == "location" and slot.get("place"):
        pl = slot["place"]
        extra = " ".join(x for x in [pl.get("built"), f"Hour: {pl['hour']}" if pl.get("hour") else ""] if x)
        if extra: where.append(extra.rstrip(".") + ".")
    slot["refs"] = refs
    parts = ["Style: " + slot["style"].rstrip(".") + ".", extra_style,
             ("Moment: " if kind in ("scene", "chapter") else "Subject: ") + base + ".",
             ("Who is in it, drawn exactly like this: " + " ".join(who)) if who else "",
             ("Where: " + " ".join(where)) if where else "",
             ("Match the attached reference pictures for " + ", ".join(n for n, _ in refs) + " (same face, costume and colours).") if refs else "",
             FRAMES.get(kind, "Illustration."), RULES]
    return re.sub(r"\s+", " ", " ".join(x for x in parts if x)).strip()
