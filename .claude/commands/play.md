Run the active campaign live at the table, following CLAUDE.md job 3.
Read the state, the current chapter, its dm/ folder and the party's sheets. Open or continue the
live log in `campaigns/<id>/sessions/NNN-live.md`. Start with the recap or the next scene's
read-aloud text, the kids' missions and the choices, then wait for the DM to tell you what the
players did. Keep each reply short. Before any roll, explain it to the kids first: the die, the
number to beat, their bonus and why, what success and failure mean. Then the kid rolls their own
die and the DM tells you the number. Roll with `python tools/roll.py --label "<who and why>"` only
when the DM asks you to. If the DM says a roll succeeded or failed, take it and move on.
When a fight is won, reveal its payoff picture (CLAUDE.md job 3) and show it.
Append to the live log after every beat and commit every few beats.
$ARGUMENTS
