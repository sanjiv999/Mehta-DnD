# Mehta Family D&D

A family tabletop role-playing game that you play by talking to Claude, with a website that
shows everyone where the story is. Four worlds, twenty-three chapters, about sixty hours of
play, written for two parents, a seven-year-old and a five-year-old.

**Nobody installs anything.** You talk to Claude in Claude Code with this repository open.
Claude narrates, rolls the dice, writes everything down, and pushes. GitHub builds the website.
The family looks at the website.

## How you play

| Moment | What you do | What Claude does |
|---|---|---|
| First night | Open the repo in Claude Code and type `/start` | Explains the world, then builds each hero by asking questions (`/hero Keisha, age 5`) |
| Before a session | `/recap` | Reads the state and gives you a recap to read aloud, the next scenes, and the kids' missions |
| At the table | `/play`, then tell Claude what the players decide | Narrates each scene, calls for rolls, resolves them, keeps a live log |
| After | `/ingest` (or just say "we're done") | Writes the session log, updates every hero and journal, awards badges, pushes |
| Any time | `/status`, `/pictures`, `/switch moon-road` | Tells you where you are; gives you picture prompts; moves between worlds |

The website updates itself a minute after each push to `main`.

## The website

- **Dashboard**: where we are, the party, open threads, which world is active.
- **Hero pages**: sheet, powers, pack, journal in the hero's voice, portrait history, badges.
- **Play decks**: one slide per scene with read-aloud text, the kids' missions, big choice buttons. Open on the TV or tablet.
- **Campaign pages**: chapters, an illustrated map that lights up visited places, people, places, sessions.
- **Story So Far**, **Sticker Book**, **Dice** for phones, **Rules**, and a **Make a hero** wizard the kids can tap through (it copies the result for Claude).
- Everything fits a phone and can be added to a home screen.

## Pictures

Claude gives you prompts (`/pictures`). You paste them into the Gemini or Claude app, save the
picture with the file name Claude names, and either upload it on the GitHub website into
`campaigns/<world>/images/` (or `characters/<hero>/portraits/`) or hand it to Claude. The site
shows placeholder art in each world's colours until then, so nothing is ever blank. No API keys.

## The worlds

| Id | Title | Setting | Chapters |
|---|---|---|---|
| `peacock-throne` | The Peacock Throne | Fantasy Mughal Hindustan: a throne losing its colours | 5 |
| `moon-road` | Lanterns of the Moon Road | Fantasy Japan: relight the pilgrim road's lanterns | 6 |
| `emberwood` | The Emberwood | Classic fantasy: a forest, a child wizard, a tired dragon | 6 |
| `starfall` | Starfall Station | Space opera: a singing nebula and first contact | 5 + finale |

Play them in any order, pause and resume, carry heroes between worlds with one keepsake each,
and collect the four pieces of the Lantern of Many Roads. The finale assembles it.

## What is in the repository

| Folder | What it holds |
|---|---|
| `characters/` | One folder per hero: sheet, journal, portraits |
| `campaigns/` | Each world: chapters as scene decks, people, places, sessions, state, pictures, DM-only notes |
| `state/world.yaml` | Which world is active, who is in the party, Lantern pieces |
| `rules/` | Family rules, kids mode, classes, combat, dice, crossings |
| `dm/` | Random tables, prompt templates, picture prompt sheet, transcripts |
| `CLAUDE.md`, `.claude/commands/` | What Claude knows and the slash commands |
| `tools/`, `site/`, `.github/` | The machinery Claude and GitHub run: validation, site build, dice, images, evaluation |

## One-time setup

1. GitHub → Settings → Pages → Source: **GitHub Actions**. The site builds on every push to `main`.
2. Open the repository in Claude Code and type `/start`.

Optional: set `publish_dm_screen: true` in `state/world.yaml` and Claude's DM screen (your notes,
stat blocks, secrets and picture prompts on the same slides) is served at `/dm/` on the site.
Anyone with the link can read it, so leave it off if a player might peek.

More: `docs/PLAYBOOK.md` (a game night, step by step), `docs/DESIGN.md` (why it is built this
way), `docs/ARCHITECTURE.md`, `docs/IMAGES.md`, `docs/NO-API.md`, `docs/TOOLS.md` (the commands
Claude runs), `docs/EVALUATION.md` (how the whole thing is tested), `docs/WRITING.md` (how the
stories are written, and the machine-writing tells they must avoid).
