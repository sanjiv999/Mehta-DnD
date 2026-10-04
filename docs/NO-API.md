# Running everything on subscriptions only (no API keys)

Nothing in this repository needs an API key. Every pipeline has a copy-and-paste route that works
with the Claude and Gemini apps you already pay for, and with GitHub's own website. The optional
workflows that call paid APIs never run unless you start them by hand.

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

1. `python tools/build_site.py --dm` and open `_site_dm/prompts.html`. It lists every missing
   picture in a sensible order (covers, chapter covers, people, places, scenes, hero portraits)
   with a Copy button and the file name to save as.
2. Paste into Gemini (or Claude). Download the one you like. Name it as shown, or leave the
   download's name alone and just make sure the slot name is somewhere in it: `Gemini_ch01-s3.png` works.
3. `python tools/images.py intake ~/Downloads --move`. It files each picture into the right campaign
   folder, writes a sidecar with the prompt, and records hero portraits on their sheets.
4. Rebuild, commit, push.

Twenty minutes of pasting covers a campaign's first chapter, its people and its places.
Tick the ones you have done on the Prompts page; ticks are remembered on that device.

If you are on a phone with no terminal: upload the pictures through GitHub's web interface into
`campaigns/<id>/images/` with the slot name as the file name. The next build picks them up; the
sidecar is optional.

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
