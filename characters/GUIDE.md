# Making your hero: a walkthrough

This is an open-ended conversation, not a form. The DM (or Claude) asks, the player answers in
any words they like, and after each answer they get **three exciting suggestions** to react to.
Nothing is locked until the player says "yes, that's my hero."

For a five-year-old, use only the **bold** questions and let them point at pictures.
For a seven-year-old, use the bold ones plus any they find interesting.
Grown-ups get the whole thing.

## Part 1: The spark

1. **If you could be any kind of creature or person in a story, what would you be?**
   (person, elf, tiger-person, robot, fairy, dragon-kid, something you make up)
2. **What is the coolest thing you can do?**
   (fight with a sword, shoot arrows, do magic, talk to animals, sneak, build gadgets, sing songs that help)
3. **Who or what do you love most?** (a pet, a sister, a grandmother, a city, the sea)
4. **What are you a little bit scared of?** (It is fine to have none.)
5. **What do you want more than anything?** (treasure, to fly, to find someone, to be the bravest)

The DM now suggests three hero ideas that combine the answers, each in one sentence with a
name and a picture in words. Example for "tiger-person, sneaky, loves her little sister, scared
of thunder, wants to fly":

- *Zara the tiger-kin rogue, who climbs anything and keeps a feather from a giant eagle she once saw.*
- *Kavi the fairy ranger, with a pet mongoose and a map to the sky.*
- *Rani the tiger-kin bard, whose drum is so loud it scares the thunder away.*

The player picks one, mixes them, or says "none of these" and the DM tries again.

## Part 2: Shape

6. **What does your hero look like?** Hair, eyes, clothes, favorite colors, one special detail
   (a scar, a pet on the shoulder, glowing hands). This becomes the portrait.
7. **Three powers.** The player names them in their own words. The DM maps each to a class power
   or spell from `rules/classes.md` and writes the mapping on the sheet.
8. **One treasure you already own.** This is the hero's keepsake and travels between worlds.
9. Pick a **class** and **species** from `rules/classes.md` that match (DM does this for kids).
10. Assign the standard array **15 14 13 12 10 8** to the six abilities. Rule of thumb: the
    highest goes to the thing they said was coolest.
11. Pick four trained skills.

## Part 3: Story

12. Where do you come from? One place, one smell, one sound.
13. Why did you leave? (Someone needs help, you got lost, you were sent, you wanted adventure.)
14. Who in the party do you already know, and how? Every hero knows at least one other.
15. What would make your hero cry with happiness? (This becomes the dream.)

## Part 4: Write it down

- Copy `characters/_template/` to `characters/<id>/`.
- Fill in `character.yaml`. Compute HP and AC with `rules/classes.md`.
- Write the "Before the story" journal entry in the hero's voice, three to five sentences.
- Run `python tools/portrait_prompt.py <id>` and generate the first portrait.
- Set `status: active` and add the id to `party:` in `state/world.yaml`.
- `python tools/validate.py`.

## Suggestion decks

If a player is stuck, draw three from the matching table:

```bash
python tools/roll.py --table hero-seeds -n 3
python tools/roll.py --table powers-kids -n 3
python tools/roll.py --table keepsakes -n 3
```
