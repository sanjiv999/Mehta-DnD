# Mehta Family D&D

A modular, file-based tabletop role-playing system that lives entirely in this repository and
renders itself into a GitHub Pages site. Four worlds, twenty-three chapters, roughly sixty hours
of play, written for a table of two parents, a seven-year-old and a five-year-old.

| Layer | What it holds | Where |
|---|---|---|
| Heroes | One folder per character: sheet, journal, portrait history | `characters/` |
| Campaigns | Self-contained worlds: chapters as scene decks, NPCs, places, sessions, state, images | `campaigns/` |
| Global state | Active campaign, party, counters, Lantern pieces | `state/world.yaml` |
| Rules | Family rules, kids mode, classes, combat, dice, crossings | `rules/` |
| DM screen | Random tables, prompt templates, transcripts | `dm/` |
| Tools | Dice, validator, campaign lifecycle, session prep, images, ingest, site build | `tools/` |
| Website | Templates and static assets rendered to `_site/` (public) or `_site_dm/` (DM screen) | `site/` |

## The worlds

| Id | Title | Setting | Chapters | Hours |
|---|---|---|---|---|
| `peacock-throne` | The Peacock Throne | Fantasy Mughal Hindustan: a throne losing its colours | 5 | ~15 |
| `moon-road` | Lanterns of the Moon Road | Fantasy Japan: relight the pilgrim road's lanterns | 6 | ~15 |
| `emberwood` | The Emberwood | Classic fantasy: a forest, a child wizard, a tired dragon | 6 | ~15 |
| `starfall` | Starfall Station | Space opera: a singing nebula and first contact | 5 + finale | ~15 |

Play them in any order. Pause and resume. Heroes cross between worlds carrying one keepsake,
collecting the four pieces of the Lantern of Many Roads. The series finale assembles it.

## What the website does

- **Dashboard**: where we are, the party, open threads, the campaign switcher.
- **Play decks**: one slide per scene with read-aloud text, the kids' missions, big choice buttons,
  a music mood, and the scene's picture. The DM build adds notes and stat blocks on the same page.
- **Campaign pages**: chapters, an illustrated map that lights up visited places, people, places, sessions.
- **Hero pages**: sheet, powers, pack, journal, portrait history, badges. Printable.
- **Story So Far**: every session recap in order, illustrated. **Sticker book**: every hero moment.
- **Hero builder**: the open-ended walkthrough as a tablet wizard; downloads a `character.yaml`.
- **Dice** and oracle for phones.

## Quick start

```bash
pip install -r requirements.txt
python tools/validate.py
python tools/build_site.py && python -m http.server -d _site 8000          # the public site
python tools/build_site.py --dm && python -m http.server -d _site_dm 8001   # the DM screen (never publish)
python tools/campaign.py status
python tools/session.py prep
python tools/roll.py d20 --adv
python tools/images.py sheet --campaign peacock-throne       # prompts to paste into Gemini/Claude
python tools/images.py intake ~/Downloads                     # file the pictures you downloaded
```

## The loop

1. **Session Zero**: build heroes with `build.html` or Claude (`dm/prompts/character-builder.md`); generate portraits.
2. **Prep**: `session.py prep` and the DM deck.
3. **Play**: deck on the TV, dice on a phone, recording on in Claude.
4. **Ingest**: drop the transcript in `dm/transcripts/` and ask Claude Code, or `ingest.py prompt` → paste into a chat app → `ingest.py apply`.
5. **Illustrate**: copy prompts from the Prompts page into Gemini or Claude, then `images.py intake ~/Downloads`.
6. **Publish**: push to `main`; the site rebuilds.

Full detail: `docs/PLAYBOOK.md`, `docs/ARCHITECTURE.md`, `docs/IMAGES.md`, `docs/DESIGN.md`.

## No API keys

Everything runs on subscriptions you already have plus GitHub Pages. Pictures: copy prompts from
the DM build's Prompts page into Gemini or Claude, download, `images.py intake`. Transcripts: ask
Claude Code, or `ingest.py prompt` → paste → `ingest.py apply`. See `docs/NO-API.md`.
The three workflows that call paid APIs are optional, manual-only, and can be deleted.

## Enabling the website

Settings → Pages → Source: **GitHub Actions**. The `pages` workflow deploys on every push to `main`.
