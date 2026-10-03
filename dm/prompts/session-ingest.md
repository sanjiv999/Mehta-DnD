# Prompt: ingest a session recording

Use with Claude after a game. Paste the transcript or point to the file.

---
You are the co-DM for this repository (read CLAUDE.md). Ingest the session recording at
`dm/transcripts/<FILE>` for campaign `<CAMPAIGN_ID>`, session number `<N>`.

Before writing anything, read: `state/world.yaml`, `campaigns/<CAMPAIGN_ID>/state.yaml`,
the current chapter file, and each party member's `character.yaml`.

Then produce, as file edits:
1. `campaigns/<CAMPAIGN_ID>/sessions/<NNN>-<slug>.md` using the session template. The
   transcript is messy; keep only what happened in the fiction, decisions the players made,
   dice results that were said aloud, and jokes worth remembering.
2. Updated `state.yaml`: chapter, location, world_date, open_threads (add, resolve), recent_events
   (keep the last five), next_hook (a question), reputation changes, flags.
3. For each hero present: hp/xp/level/inventory/conditions/relationships/achievements in
   `character.yaml`, and a dated first-person journal entry of three to six sentences in that
   hero's voice (for Kids Mode heroes, use short words and one exclamation mark at most).
4. `state/world.yaml`: session_counter, last_played.
5. If a hero's look changed, append a dated prompt block to their `portraits/prompt.md`.
6. In the session log's DM feedback: pacing (too fast/slow where), one sentence on what each
   player enjoyed most, loose ends, three ideas for next time, and anything a child seemed
   unsure or upset about so the DM can check in.

Do not invent events that did not happen. Where the transcript is unclear, write `[unclear: ...]`
and ask me at the end. Finish by running `python tools/validate.py`.
