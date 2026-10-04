# Playbook: running a game night

## Before (10 minutes)

1. `python tools/campaign.py status` to confirm the active campaign and chapter.
2. `python tools/session.py prep` for the brief, or ask Claude to prep (dm/prompts/session-prep.md).
3. Build the DM screen: `python tools/build_site.py --dm && python -m http.server -d _site_dm 8001`,
   then open `http://localhost:8001/play/<campaign>/<chapter>.html`. This is the player deck
   with your DM notes, complications and stat blocks on the same page. Never publish `_site_dm`.
4. Put the public site on the TV or a tablet: the same deck without the notes. Phone: `dice.html`.

## During (30 to 75 minutes depending on who is at the table)

- Open with the recap in second person. Let the kids finish the sentences.
- Start recording in Claude. Say "Session N, campaign X, date" at the top.
- Advance the deck one scene at a time. Read the read-aloud. Hand out the missions. Let the kids
  tap the choice buttons on the tablet; a tapped button is their declared action.
- Say dice results and state changes out loud ("Arya rolled 17", "the party now has the key").
- Use the difficulty ladder. Default to Tricky (13).
- Every fifteen minutes give the five-year-old a mission from the slide.
- If a scene stalls, roll the chapter's d6 complication table.
- End on the chapter's cliffhanger or the next scene's first line.

## After (15 minutes, mostly Claude)

Two ways, pick one:

**Interactive.** Save the transcript as `dm/transcripts/NNN-YYYY-MM-DD.md`, then ask Claude Code:
"Ingest `dm/transcripts/NNN-....md` for the active campaign." It follows CLAUDE.md and edits the files.

**Automatic.** Commit the transcript and push. The ingest workflow runs `tools/ingest.py` with the
Anthropic API and opens a pull request with the session log, state and journal changes.

Then: review the diff, fix anything the kids would dispute, run `python tools/validate.py`,
merge or push to `main`. The site rebuilds. If the session log has an `image_prompt`, the next
image run illustrates it for the Story So Far page.

## Session Zero (the first night)

1. Open `build.html` on the tablet. Each player walks through the hero builder; it writes a
   `character.yaml` to download. Or sit with Claude and dm/prompts/character-builder.md.
2. Drop each file into `characters/<id>/character.yaml`, add the ids to `party:` in `state/world.yaml`.
3. `python tools/images.py heroes` for portraits (or paste the prompt from
   `python tools/portrait_prompt.py <id>` into any image tool).
4. Read the campaign's pitch from the overview. Play scene 1 of chapter 1 if there is time.

## Switching campaigns

```bash
python tools/campaign.py pause --note "left at the kappa"
python tools/campaign.py switch moon-road
python tools/campaign.py resume peacock-throne
python tools/campaign.py complete peacock-throne     # counts a Lantern piece
```

Each switch writes a Crossing stub into every party journal. Fill it in (or let the ingest do it).

## Adding or removing a player

Edit `party:` in `state/world.yaml`. Heroes not in the party rest on the website and can return any time.
