# Writing: how the stories are written, and how to tell when they are not

Every piece of narrative in this repository (read-aloud text, NPCs, places, overviews, journals,
session logs) is held to this document. It exists because the first drafts were competent and
hollow: a sentence of colour here, a simile there, nothing a reader could stand inside. This is
the fix, drawn from people who know (Le Guin's *Steering the Craft*, Orwell's six rules, Elmore
Leonard's ten, Sly Flourish's lazy-DM prep, the Alexandrian on NPCs and clues, the people who
write and run games for small children) and from the known habits of machine prose.

## The order of work

**Depth first, description last.** Never write a description to fill a slot. Before a place is
described, know: who built it, who keeps it, what is traded or grown or hidden there, what it
smells like at dawn versus dusk, what breaks there, who sleeps there. Before a person speaks,
know what they want this week, what they are afraid of, the thing they do with their hands, the
one belief they will not say aloud, and who they disagree with. The world bible in each campaign
folder (`campaigns/<id>/world.md`) holds this. Descriptions are then *selected* from it, not invented.

**Grounding before invention.** The worlds borrow from real places and times (Akbar's Sikri, the
Nakasendō post towns, a medieval market village, a working station). A real detail (the Nauroz
weighing of a ruler against grain and silver, a kappa's dish of water, the communal bread oven,
velcro on every surface in zero gravity) outweighs ten invented ones, because a reader can feel
when something was observed rather than assembled.

## Rules for read-aloud text

1. **Two to five sentences, under 90 words.** Longer and the table stops listening.
2. **One thing a person could do, right now.** The last sentence hands the players the scene.
3. **Senses in this order: what is obviously there, what it is doing, what is wrong.** Not a list
   of pleasant nouns; a situation.
4. **Nouns that could not be anywhere else.** "Turmeric footprints" beats "colourful footprints".
   "A cheetah on a leash, hooded, asleep in the shade of a palanquin" beats "a cheetah".
5. **Verbs do the work.** Cut adjectives until the sentence limps, then put one back.
6. **No metaphor unless it is the only way to say it.** A metaphor earns its place by being
   *truer* than the literal, not prettier. Test: would a tired parent reading this at 7pm trip on it?
7. **Never tell the players what they feel.** "You feel a chill" is theft. Describe the draft.
8. **Children get the concrete object.** A five-year-old can hold "a golden bell the size of a
   walnut". She cannot hold "an air of mystery".
9. **Read it aloud before saving.** If it sounds like writing, rewrite it (Leonard).

## Rules for people

- **A want, this week.** Not "wants justice": "wants her brother's elephant back before the
  parade at sunset, so the vizier never learns the gate was unlatched."
- **A fear that is specific** and that the want runs into.
- **A habit of the hands or the voice** the DM can do at the table. One, not three.
- **A contradiction.** The polite oni. The vain rakshasa who is lonely. The AI who runs a station
  and cannot remember lunch.
- **An opinion about one other person in the world**, preferably unfair.
- **A history that explains the want** in two sentences the DM can reveal later.
- Dialogue: people interrupt themselves, answer the wrong question, and do not explain their
  motives. Nobody says "I am lonely."

## Rules for places

- Built by someone, for something, and now used for something else.
- **What time of day is it, and what is the light doing.** Pick one. Sikri at noon is not Sikri at the hour the kites come down.
- Three things a visitor sees first, in the order they would see them.
- One sound and one smell, specific to this place and this hour.
- Something recently changed, that a child could notice.
- Who is here now and what they are in the middle of doing.

## Rules for the DM-facing notes

Plain, short, honest. Numbers, difficulties, outcomes. Jokes allowed. No atmosphere.

## The tells (do not write these)

Drawn from the Wikipedia "Signs of AI writing" page and from reading our own first drafts.

**Vocabulary to avoid in narrative:** tapestry, testament, delve, vibrant, bustling, nestled,
in the heart of, a symphony of, whispers of, echoes of, canvas, realm, journey (as metaphor),
unleash, elevate, intricate, enchanting, breathtaking, mesmerising, timeless, ethereal, palpable,
myriad, plethora, beacon, dance (as a verb for anything that is not dancing), weave, embrace
(as a verb for things), "a world of", "a sense of", "the very", "mere", "shimmering",
"glistening" (unless wet), "ancient" (as a vague intensifier).

**Structures to avoid:**
- Three of everything. "Drums. Kites. Sugar-cane." Two is a pair, four is a list, three is a tic.
- "Not X but Y" and "it is not just X, it is Y."
- "Something ancient/enormous/old" without saying what.
- "Like a X that decided to be a Y."
- Sentences ending in a trailing "-ing" clause that explains the sentence you just read.
- Starting with the weather (Leonard) unless the weather is the plot.
- Ending a description on a vague portent ("...and somewhere, something waited").
- The size-of comparison as a reflex ("the size of a house", "bigger than the town hall").
- "In a voice like X" for every character.
- Em dashes in read-aloud text; the DM cannot speak an em dash.

**Rhythm to avoid:** every sentence the same length; every paragraph ending on a reveal; the
short-sentence-for-drama trick more than once a scene.

## What good looks like

Bad: *The bazaar is a canyon of colour. Spice pyramids as tall as you, silk awnings, a hundred
voices bargaining.*

Better: *The Shahi Bazaar runs downhill under cloth awnings so low the grown-ups duck. A spice
seller is shouting prices at a woman who has not asked. Someone has walked straight through
his turmeric: big round prints, elephant-sized, yellow all the way down the hill.*

The second one has a direction (downhill), a scale (the adults duck), a person doing a thing
(shouting at someone who has not asked), and the clue in a form a five-year-old can follow.

## Checking

`python tools/prose_lint.py` scores every narrative file for the tells above and prints the
worst offenders with line numbers. It is a smoke alarm, not a judge: a flagged word is a prompt
to re-read the sentence, and a clean file can still be hollow. The evaluation runs it and fails
the build if the density rises above the ceiling in `tools/prose_lint.py`.
