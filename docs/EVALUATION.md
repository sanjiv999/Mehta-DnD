# Evaluation loop

`python tools/evaluate.py` plays a pretend first month with the system, on a throwaway copy of the
repository, and reports what broke. It is the thing to run after changing a tool, a template, or
the site, and it runs on every pull request through the `evaluate` workflow (no API keys).

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m playwright install chromium        # once; the browser checks need it
python tools/evaluate.py                     # about three minutes
python tools/evaluate.py --no-browser        # faster, skips decks and phone checks
python tools/evaluate.py --keep              # keep the scratch copy to poke at
```

The report lands in `_eval/report.md` with screenshots in `_eval/shots/`.

## What it simulates

| Stage | What happens | What is checked |
|---|---|---|
| Content | Parses all 23 chapters | every scene has read-aloud text, a kids' mission, two or more choices and art direction; every chapter has a six-entry complication table, rewards and an ending; 190 image slots enumerate |
| Dice | Rolls thousands of dice | seeds reproduce, d20 spans 1 to 20 with a fair mean, advantage raises it, modifiers add, every table rolls, the oracle answers, rolls are logged |
| Keisha makes a hero | Scripted answers to the CLI builder | the sheet is written, kids mode set, the "coolest thing" picks the class and the highest ability, HP and AC follow the rules, three powers and a keepsake, a first-person journal, the repo validates, the portrait prompt names her and uses the world's art style |
| Arya makes a hero | A real browser walks all 17 steps of the web wizard on a phone-sized screen | no JS errors, the downloaded YAML parses, INT is highest for a mage, skills and powers carry over, the sheet validates once dropped into the repo |
| Two sessions | Prep brief, a session log from the template, two transcripts turned into prompt files, synthetic replies built from the chapter's own scenes, applied through the no-API ingest | the prompt bundles state, heroes, schema and transcript; dry run changes nothing; logs, state, XP, items, badges, journals, world counter and the ingested marker all update; the repo validates after each; a malformed reply is rejected with field names; Story So Far, sticker book, hero page, campaign page and dashboard all reflect the sessions; decks appear exactly for the chapters reached |
| Pictures | The prompt sheet, hero prompts, and an intake folder with files named by sheet number, by slot with a campaign hint, by NPC, and a hero portrait, plus a stray text file | generate refuses without a provider; intake files each picture correctly, moves only what it filed, records the portrait; the deck uses the real picture; the DM prompts page lists only what is still missing |
| Conversation | Checks the slash commands and CLAUDE.md, an uploaded portrait with no sheet edit, the DM screen at `/dm/`, the wizard's Copy for Claude | the whole loop is reachable by talking; nothing requires the family to run code |
| Secrets | Collects every `secret:` field, `## Secret` section and DM-folder line | none appear anywhere in the public build; most appear in the DM build |
| Lifecycle | switch, pause with a note, resume, complete, new | statuses, crossing stubs in every journal, history, the resume note, a Lantern piece, a scaffolded fifth world that validates and builds |
| Browser | Every slide of every deck in the DM build, the dice page, then every page type at 390×844 | each slide has read-aloud text, a choice can be picked, the counter ends at N/N, no JS errors; d20 and oracle work; no horizontal scrolling, every tap target at least 40px, no JS errors on phones |

About 360 checks. The first run found fourteen problems, including two finale chapters without
complication tables, a chapter template that could not validate when scaffolded, a rules page
that overflowed on phones, and a CLI builder that did not put the highest score on the coolest
thing. All fixed; that is what the loop is for.

## Adding a check

Each stage is a function in `tools/evaluate.py` that calls `check(name, condition, detail)`.
Add one line to the stage it belongs to. Keep checks on behaviour the family would notice.
