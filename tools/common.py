"""Shared helpers: paths, YAML/Markdown loading, secret stripping."""
from __future__ import annotations
import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
CHARACTERS = ROOT / "characters"
CAMPAIGNS = ROOT / "campaigns"
STATE = ROOT / "state" / "world.yaml"
RULES = ROOT / "rules"
TABLES = ROOT / "dm" / "tables"
ROLL_LOG = ROOT / "dm" / "rolls.log"

FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)


def load_yaml(path: Path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def dump_yaml(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=100)


def load_md(path: Path) -> tuple[dict, str]:
    """Return (front_matter, body) for a Markdown file."""
    text = path.read_text(encoding="utf-8")
    m = FRONT.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    return meta, text[m.end():]


def strip_secret_section(body: str) -> str:
    """Remove a trailing '## Secret' section (and anything after it) from Markdown."""
    idx = re.search(r"^##\s+Secret\b", body, re.M)
    return body[: idx.start()].rstrip() + "\n" if idx else body


def strip_secrets(obj):
    """Recursively drop any key named 'secret' from loaded YAML."""
    if isinstance(obj, dict):
        return {k: strip_secrets(v) for k, v in obj.items() if k != "secret"}
    if isinstance(obj, list):
        return [strip_secrets(v) for v in obj]
    return obj


def world() -> dict:
    return load_yaml(STATE)


def campaign_ids() -> list[str]:
    return sorted(p.name for p in CAMPAIGNS.iterdir() if p.is_dir() and not p.name.startswith("_"))


def character_ids() -> list[str]:
    return sorted(p.name for p in CHARACTERS.iterdir() if p.is_dir() and not p.name.startswith("_"))


def load_campaign(cid: str) -> dict:
    d = CAMPAIGNS / cid
    meta = load_yaml(d / "campaign.yaml")
    meta["state"] = load_yaml(d / "state.yaml") if (d / "state.yaml").exists() else {}
    meta["dir"] = d
    meta["sessions"] = sorted_sessions(d)
    return meta


def sorted_sessions(cdir: Path) -> list[dict]:
    out = []
    for p in sorted((cdir / "sessions").glob("*.md")):
        if p.name.startswith("000"):
            continue
        meta, body = load_md(p)
        meta["body"] = body
        meta["file"] = p.name
        out.append(meta)
    return sorted(out, key=lambda s: s.get("number", 0))


def load_character(cid: str) -> dict:
    d = CHARACTERS / cid
    c = load_yaml(d / "character.yaml")
    c["dir"] = d
    c["journal"] = (d / "journal.md").read_text(encoding="utf-8") if (d / "journal.md").exists() else ""
    return c


def bonus(score: int) -> int:
    return (int(score) - 10) // 2


def fmt_bonus(score: int) -> str:
    b = bonus(score)
    return f"+{b}" if b >= 0 else str(b)
