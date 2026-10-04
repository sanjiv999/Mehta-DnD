# Design: what makes it engaging, and where the humans come in

## The shape of it
The family talks to Claude. Claude holds the rules, the worlds, the secrets and the dice, and
writes everything to plain files. GitHub turns the files into a website. The website is what the
kids look at: their hero, their badges, the map, the next scene. No one installs or runs anything;
the Python in `tools/` is Claude's and GitHub's, not the family's.

## The loop, for a five-year-old
Every scene gives Keshu a **mission that cannot fail**: find, count, name, choose, hum, hold.
These are written into every chapter as `Jobs for the kids` and appear on the play screen as
"Your missions". The dice are for the grown-ups and the seven-year-old; the five-year-old rolls
when she wants to and succeeds whenever she tries. Things she names become canon forever (camels,
dishes, songs, the ship's paint job) and show up on the website the next day.

## The loop, for a seven-year-old
Aarya gets **secrets and spotting**: the footprint going the wrong way, the maker's mark, the map
that draws itself. One new mechanic per session. She reads the choice buttons aloud. She tells
the story when someone loses at chess. She gets a hero moment badge most sessions and can see
her sticker book grow.

## The loop, for the parents
Real choices with consequences (reputation, allies who show up in finales, items that matter
three chapters later), a mystery per campaign with an answer that recontextualises the start,
and villains who are redeemable rather than killable. Every finale is a conversation that looks
like a fight. The DM has a brief, a deck, stat blocks on the same screen, and a d6 table when a
scene stalls.

## Where the human spark is required
| Moment | What the system does | What the human does |
|---|---|---|
| Making a hero | Asks the questions, offers three ideas each time, computes the sheet | The kid's answers and drawing |
| Scene art | Composes a consistent prompt for every slot, placeholders meanwhile | Pastes into Gemini or Claude, picks the best, overrides prompts, scans the kids' drawings |
| Running a session | Deck with read-aloud, missions, buttons, music chips, DM notes | Voices, pacing, improvisation, saying yes |
| After a session | Claude Code (or a pasted prompt) turns the transcript into logs, state, journals, badges | Reviews the diff, fixes what the kids would dispute |
| Between campaigns | Crossings, keepsakes, the Lantern | Deciding what the fifth world is |

## Why files
Everything is text so that any of it can be changed by a person or by Claude with the same
tools, so that history is a git log, and so that the site can be rebuilt from scratch forever.

## Pacing targets
| Table | Session length | Scenes per session | Fights |
|---|---|---|---|
| With the five-year-old | 30 to 45 min | 2 | at most 1, short |
| With the seven-year-old | 45 to 60 min | 3 | 1 |
| Grown-ups only | 90+ min | 4 or more | as written |

Each chapter lists `sessions_estimate` and `hours_estimate` in its front matter; the campaign
page sums them. The four campaigns total roughly 60 hours of play.

## Things we deliberately do not do
No character death. No permanent loss of a kid's named thing. No villain who cannot be talked
to. No scene where a kid has nothing to do. No reading ahead required: the deck shows one
scene at a time.
