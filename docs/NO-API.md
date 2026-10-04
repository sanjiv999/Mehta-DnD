# Running everything on subscriptions only (no API keys, no installs)

Nothing in this repository needs an API key, and the family never runs code. Claude Code (part of
a Claude subscription) runs the tools; GitHub builds the site; pictures come from the Gemini or
Claude apps by copy and paste. The optional workflows that call paid APIs never run unless you
start them by hand. The commands below are what Claude runs when you ask.

## What uses what

| Task | Free route | Where |
|---|---|---|
| Prep a session | `python tools/session.py prep`, or ask Claude Code | local |
| Play | the public site on a TV or tablet, the DM build on your laptop, dice on a phone | local / GitHub Pages |
| Ingest a transcript | **Claude Code** (included in Claude Pro): "ingest dm/transcripts/NNN.md" | Claude Code |
| Ingest without Claude Code | `ingest.py prompt` writes one prompt; paste into claude.ai or Gemini; `ingest.py apply` the JSON reply | local + any chat app |
| Hero portraits | `images.py heroes --prompts`; paste into Gemini; save as `portrait-<id>.png`; `images.py intake` | local + Gemini/Claude |
| Scene and NPC art | `images.py sheet` (or the DM build's Prompts page with copy buttons); paste; save; `images.py intake` | local + Gemini/Claude |
| Build a hero | `build.html` on a tablet, or Claude Code with the character-builder prompt | site / Claude Code |
| Publish | push to `main`; GitHub Pages builds for free | GitHub |

Claude Code sessions count against your Claude subscription, not a separate bill. Gemini image
generation in the Gemini app is part of Gemini Pro. Neither needs a key in this repo.

## The picture loop in practice

1. Open `PICTURES.md` at the top of the repo (GitHub shows it on a phone). It lists every missing
   picture, most needed first: the current chapter's cover and scenes, the people and places in
   it, then the heroes. Each entry has a number, the aspect ratio, any reference pictures to attach
   first, and the prompt in a box with a copy button.
2. Paste the prompt into Gemini (or Claude). If the entry names reference pictures, attach those
   first so the face and costume match. Save the one you like as the number (`07.png`).
3. Upload it to the `inbox/` folder on GitHub (**Add file → Upload files**). A workflow files it
   into the right campaign, records hero portraits, refreshes `PICTURES.md` and rebuilds the site.
   Or paste the pictures into the chat with Claude and say the numbers; Claude runs
   `python tools/images.py intake <folder> --assign 07,12,13`.
4. That is the whole loop. Nothing to approve, nothing to install.

Twenty minutes of pasting covers a chapter's cover, its scenes, its people and the heroes, which
is what the kids see first. `python tools/session.py prep` lists what the next chapter still needs.

## The transcript loop in practice

**With Claude Code** (recommended): open the repository, say
"Ingest dm/transcripts/003-2026-11-02.md for the active campaign." It reads CLAUDE.md, writes the
session log, updates state and every hero, appends journals, and runs the validator. Review the diff.

**With the chat apps**:

```bash
python tools/ingest.py prompt dm/transcripts/003-2026-11-02.md     # writes 003-2026-11-02.prompt.md
# paste that file into claude.ai or Gemini; save the JSON reply as reply.json
python tools/ingest.py apply dm/transcripts/003-2026-11-02.md reply.json --dry-run
python tools/ingest.py apply dm/transcripts/003-2026-11-02.md reply.json
python tools/validate.py
```

The prompt file carries the campaign state, the chapter, every hero sheet, the rules summary and
the transcript, so the model has everything. The reply is validated against a schema before
anything is written; if a field is missing, the error says which, and you ask the model to fix it.

## Recording the session

Record with whatever you have: the Claude app's voice mode, a phone voice memo transcribed by
Gemini, or typed notes. Save the text as `dm/transcripts/NNN-YYYY-MM-DD.md`. The ingest does not
care how clean it is; it lists anything unclear at the end.

## What the optional workflows are for

`images.yml`, `portrait.yml` and `ingest.yml` exist in case you ever decide an API is worth it.
They only start from the Actions tab, they fail harmlessly without a secret, and each opens a pull
request rather than touching `main`. You can delete them with no effect on anything else.
