# Playbook: running a game night

## Before (10 minutes)

1. `python tools/campaign.py status` to confirm the active campaign.
2. `python tools/session.py prep > /tmp/brief.md` and read it, or ask Claude:
   "Prep session N of the active campaign."
3. Print or open each hero's page on the website so the kids can see their portrait.
4. Choose one scene per hero where they are the star.

## During (45 to 75 minutes with kids)

- Open the recap with "Last time, you..." in second person. Let the kids finish sentences.
- Start recording in Claude. Say "Session N, campaign X, date" at the top.
- Say dice results out loud ("Arya rolled a 17") so the transcript captures them.
- Say state changes out loud ("The party now has the brass key").
- Use the difficulty ladder in `rules/family-rules.md`. Default to "Tricky (13)".
- Every 15 minutes give a five-year-old job: find, name, choose, or roll.
- End on a cliffhanger question and write the answer-to-be in your notes.

## After (15 minutes, mostly Claude)

1. Save the transcript as `dm/transcripts/NNN-YYYY-MM-DD.md`.
2. Ask Claude: "Ingest `dm/transcripts/NNN-....md` for the active campaign." It follows
   `CLAUDE.md` section 3 and edits the files.
3. Review the diff. Fix anything the kids would dispute.
4. If a portrait should change, run `python tools/portrait_prompt.py <id>` and generate.
5. `python tools/validate.py`, commit, push.

## Switching campaigns

```bash
python tools/campaign.py pause                # park the active campaign with a resume note
python tools/campaign.py switch moon-road     # make another one active (starts it if needed)
python tools/campaign.py resume peacock-throne
```

Each switch writes a Crossing entry so the heroes' journals explain how they travelled.

## Adding or removing a player

Edit `party:` in `state/world.yaml`. A hero not in the party stays on the website under
"Resting heroes" and can rejoin any time.
