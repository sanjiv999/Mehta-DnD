# Tools (run by Claude and by GitHub, not by the family)

Everything here is a plain Python script with no services behind it. Claude runs them inside
Claude Code; the GitHub workflows run them on every push. Listed so Claude knows what exists.

| Tool | What it does |
|---|---|
| `tools/validate.py` | Checks every YAML and chapter file. Run after every edit. |
| `tools/build_site.py [--dm] [--out DIR]` | Renders the website. `--dm` adds DM notes, secrets and the prompt sheet. |
| `tools/roll.py` | Dice, tables and the oracle. The only source of randomness. Logs to `dm/rolls.log`. |
| `tools/campaign.py status\|switch\|pause\|resume\|complete\|new` | Campaign lifecycle; writes Crossing stubs. |
| `tools/session.py prep\|new` | DM brief for the next session; a session log from the template. |
| `tools/new_character.py` | Interactive hero builder (the conversational route in CLAUDE.md is preferred). |
| `tools/portrait_prompt.py <id> [--record FILE]` | Portrait prompt from the sheet and the world's art style; record a saved portrait. |
| `tools/prose_lint.py [paths] [--strict] [--show N]` | Score player-facing prose for the tells of machine writing (banned words, triplets, "not X but Y"); `--strict` fails above the ceiling. |
| `tools/images.py sheet\|intake\|plan\|prompt\|record\|heroes` | Picture prompts and filing of downloaded pictures. No API. |
| `tools/ingest.py prompt\|apply` | A paste-ready ingest prompt and the applier for its JSON reply (for chat apps outside Claude Code). |
| `tools/evaluate.py` | The end-to-end test of everything, run on every pull request. |
| `tools/scenes.py`, `tools/common.py`, `tools/placeholder.py` | Shared parsing, paths and placeholder art. |

If a person ever wants to run them: `pip install -r requirements.txt`, then the commands above.
