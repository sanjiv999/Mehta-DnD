# Mehta Family D&D

A modular, file-based tabletop role-playing game system that lives entirely in this repository.
Characters, campaigns, sessions, rules, dice and the Dungeon Master's notes are all plain text
(YAML + Markdown) under version control. A GitHub Actions workflow renders them into a
GitHub Pages site where each player can see their active character, portrait, journal and
where the party is in the story.

| Layer | What it holds | Where |
|---|---|---|
| Players and characters | One folder per character: sheet, journal, portrait history | `characters/` |
| Campaigns | Self-contained worlds: overview, chapters, NPCs, places, sessions, state | `campaigns/` |
| Global state | Which campaign is active, who is in the party, campaign order | `state/world.yaml` |
| Rules | Family rules, kids mode, combat quick reference, dice | `rules/` |
| DM screen | Random tables, generators, prompt templates, raw transcripts | `dm/` |
| Tools | Dice roller, validators, site builder, character and campaign scaffolds | `tools/` |
| Website | Templates and static assets rendered to `_site/` and deployed to Pages | `site/` |

## Quick start

```bash
pip install -r requirements.txt
python tools/roll.py 2d6+3             # roll dice
python tools/roll.py d20 --adv         # roll with advantage
python tools/roll.py --table oracle    # consult a random table
python tools/new_character.py          # guided character builder (interactive)
python tools/campaign.py status        # where are we?
python tools/campaign.py switch moon-road
python tools/session.py prep           # DM brief for the next session
python tools/validate.py               # check every YAML file
python tools/build_site.py && python -m http.server -d _site 8000
```

## How a game night works

1. **Prep.** `python tools/session.py prep` prints a one-page DM brief: where the party is,
   open threads, each hero's status, and the hook you wrote last time.
2. **Play.** Keep `dice.html` open on a phone or run `roll.py`. Record the session with Claude.
3. **Ingest.** Drop the transcript in `dm/transcripts/` and ask Claude (which reads `CLAUDE.md`)
   to write the session log, update the campaign state and every hero's journal, award XP,
   and refresh portrait prompts if a hero changed.
4. **Publish.** Commit and push. The Pages site rebuilds automatically.

See `docs/PLAYBOOK.md` for the full loop and `docs/ARCHITECTURE.md` for how the pieces fit.

## The table

Four heroes to start: Sanjiv (also the DM), his wife, Arya (7) and Keisha (5).
`characters/GUIDE.md` is the open-ended walkthrough each player uses to invent their hero.

## Campaigns

| Id | Title | Setting | Status |
|---|---|---|---|
| `peacock-throne` | The Peacock Throne | Fantasy Mughal-era Hindustan | active |
| `moon-road` | Lanterns of the Moon Road | Fantasy medieval Japan, yokai and shrines | planned |
| `emberwood` | The Emberwood | Classic high fantasy | planned |
| `starfall` | Starfall Station | Space opera | planned |

Campaigns can be played in any order, paused and resumed. Heroes carry across campaigns
through the **Crossing** rules in `rules/crossings.md`.

## Enabling the website

Settings → Pages → Source: **GitHub Actions**. The `pages` workflow deploys on every push to `main`.
