# Architecture

## Principles

1. **Files are the database.** Every fact about the game is a YAML or Markdown file. Git history
   is the save system: any session, character or campaign can be rewound.
2. **Modular campaigns.** A campaign is a self-contained folder. Deleting or adding one never
   touches another. Heroes are global and move between campaigns via Crossings.
3. **Player-facing versus DM-facing.** Anything under `dm/` or `campaigns/<id>/dm/`, and any
   YAML key named `secret`, is never rendered to the website.
4. **Derived, not duplicated.** The website, DM briefs and portrait prompts are generated from
   the source files. Nothing is hand-maintained in two places.
5. **Reproducible randomness.** Dice and table rolls go through `tools/roll.py` and are logged.

## Data model

```
state/world.yaml                 global: active campaign, party, counters, campaign history
characters/<id>/
  character.yaml                 the sheet (see characters/_template/character.yaml)
  journal.md                     first-person entries, one per session
  portraits/prompt.md            running list of image prompts, newest last
  portraits/NNN.png              generated images
campaigns/<id>/
  campaign.yaml                  metadata: title, setting, tone, art style, status
  state.yaml                     live state: chapter, location, threads, next hook
  overview.md                    player-safe premise and world primer
  chapters/NN-slug.md            story arcs with scenes, choices and outcomes
  npcs/<slug>.md                 people, with a `secret` section for the DM
  locations/<slug>.md            places
  sessions/NNN-slug.md           what happened, with front matter
  dm/                            secrets, encounter lists, villain plans
```

## Pipelines

### Session loop
```
prep  ──▶  play (record + dice)  ──▶  ingest transcript  ──▶  commit  ──▶  site rebuild
 ▲                                                                            │
 └────────────────────────────────────────────────────────────────────────────┘
```

`tools/session.py prep` reads global and campaign state and prints the DM brief.
Ingestion is done by Claude following `CLAUDE.md` and `dm/prompts/session-ingest.md`, or automatically
by `tools/ingest.py` (Anthropic API, structured output) via the ingest workflow, which opens a pull request.

### Portrait loop
```
character.yaml + campaign art style ──▶ tools/portrait_prompt.py ──▶ prompt text
   ──▶ image model (manual paste or tools/portrait_generate.py with an API key)
   ──▶ characters/<id>/portraits/NNN.png ──▶ --record ──▶ site gallery
```

### Scene decks and the DM screen
Chapters follow a fixed Markdown convention (`tools/scenes.py` parses it): `### Scene N: Title (kind)`,
blockquotes are read-aloud, `Jobs for the kids`, `Choices` and `Music` are player-safe, `Image` is
art direction, everything else is DM-only. The public build renders a deck per active or finished
chapter at `play/<campaign>/<NN>.html`. `build_site.py --dm` renders `_site_dm/` with the DM notes,
complications, stat blocks, NPC secrets and planned chapters alongside. Never publish `_site_dm`.

### Images
Every picture is an image slot with a composed prompt (`docs/IMAGES.md`). `tools/images.py plan`
lists them, `generate` fills the missing ones through a provider, and the build substitutes a
procedural SVG placeholder (`tools/placeholder.py`) wherever a file is missing. Player art in
`campaigns/<id>/art/` overrides generated art.

### Site build
`tools/build_site.py` loads every YAML and Markdown file, strips secrets, renders Jinja2
templates from `site/templates/` into `_site/`, and copies `site/static/`. The `pages`
workflow runs it on every push to `main` and deploys with `actions/deploy-pages`.

Pages rendered:

| Page | Source |
|---|---|
| `index.html` | world.yaml + every campaign.yaml + state.yaml: the dashboard and campaign switcher |
| `characters/<id>.html` | character.yaml, journal.md, portraits |
| `campaigns/<id>.html` | campaign.yaml, overview.md, state.yaml, sessions, public NPCs and locations |
| `play/<cid>/<NN>.html` | scene deck for one chapter |
| `story.html` | every session recap in order, illustrated |
| `stickers.html` | achievements and hero moments across all sessions |
| `build.html` | the hero builder wizard; downloads a character.yaml |
| `dice.html` | dice roller and oracle, pure JavaScript |
| `rules.html` | rules/*.md |

## Extending

- **New campaign:** `python tools/campaign.py new <id> "Title"` copies `campaigns/_template/`.
- **New player:** `python tools/new_character.py` or follow `characters/GUIDE.md` with Claude.
- **New random table:** add `dm/tables/<name>.yaml` with a `entries:` list (optionally weighted).
- **New rule module:** add `rules/<name>.md`; it appears on the rules page automatically.
