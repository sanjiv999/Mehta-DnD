# Playbook: a game night, step by step

You never run a command. You talk to Claude in Claude Code with this repository open, and you
look at the website. Claude does the rest.

## Session Zero (the first night, 45 minutes)

1. Type `/start`. Claude explains the world and reads the pitch.
2. For each player, `/hero Keshu, age 5` (and so on). Claude asks one question at a time: what
   creature, what is the coolest thing you can do, who do you love, what are you scared of, what do
   you want. The grown-up relays the answers. Claude suggests three ideas after each. When the
   player is happy, Claude writes the sheet, the first journal entry, and gives you a portrait
   prompt for Gemini. Or the kids tap through **Make a hero** on the website and press
   **Copy for Claude**.
3. Paste the portrait prompts into Gemini, save each picture as `001.png`, upload to
   `characters/<hero>/portraits/` on GitHub (or hand them to Claude).
4. The site now shows four heroes. If there is time, `/play` for the first scene.

## Before a session (5 minutes)

`/recap`. Claude gives you a three-sentence recap to read aloud, the open threads, the next scenes
with each kid's mission, a d6 complication table, and two encounters with stat blocks.
Open the play deck on the TV or a tablet from the dashboard's **Play chapter** button.

## At the table (30 to 75 minutes)

1. `/play`. Claude gives you the read-aloud text, the missions and the choices for the scene.
2. Read it. Let the kids tap or shout their choice. Tell Claude: "Keshu rang the bell and Aarya
   climbed to the monkeys and rolled a 14."
3. Claude resolves it, narrates in a few sentences, and gives you the next beat. If you want
   Claude to roll, say so; it rolls with the logged dice.
4. Keep going scene by scene. Claude writes a live log as you go, so a dropped connection loses nothing.
5. Say "we're done for tonight" (or `/ingest`). Claude writes the session log, updates every
   hero and journal, awards badges, pushes, and tells you what the site will show.

Rules of thumb: default difficulty is Tricky (13); the five-year-old gets a mission every few
minutes; if a scene stalls, ask Claude for a complication; if a kid is upset, tell Claude and the
story bends.

## Between sessions

- `/status` any time to hear where you are.
- `/pictures` for the next batch of prompts; paste into Gemini; upload the pictures on GitHub.
- `/switch moon-road` to change worlds (Claude pauses the current one and writes each hero's
  Crossing); `/switch resume peacock-throne` to come back; `/switch complete <world>` when a
  world's finale is done (that counts a Lantern piece).
- To add or rest a player, tell Claude.

## If you recorded the session instead

Save the transcript as `dm/transcripts/NNN-YYYY-MM-DD.md` (upload on GitHub or paste it) and
`/ingest dm/transcripts/NNN-....md`.
