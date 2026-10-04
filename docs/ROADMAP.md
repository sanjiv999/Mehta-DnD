# Roadmap

## Done
- Repository layout, data model, templates, validation, Pages deploy
- Family rules, kids mode, classes, combat, dice, crossings, advanced options
- Character builder (guide, CLI, and the web wizard), four hero slots, worked example
- Four campaigns, 23 chapters, roughly 60 hours of play: The Peacock Throne (5), Lanterns of
  the Moon Road (6), The Emberwood (6), Starfall Station (5 + series finale)
- Scene decks for play, DM screen build, illustrated maps, Story So Far, sticker book
- Image pipeline: slots, consistent prompts, placeholders, generation, overrides, player art, PR approval
- Transcript ingest: interactive (CLAUDE.md) and automatic (workflow + Anthropic API)
- Dice roller, oracle and random tables (CLI and web)
- Evaluation harness (tools/evaluate.py) covering content, dice, both hero builders, two simulated sessions, pictures, secrets, lifecycle, decks and phones
- Mobile layout, home-screen manifest

## Next
- [ ] Session Zero: build the four heroes, generate portraits, play chapter 1
- [ ] First image batch: covers, chapter covers, Peacock Throne NPCs and places
- [ ] Tune kids-mode difficulty from real rolls in `dm/rolls.log`
- [ ] Session recap illustrations after each session (`image_prompt` in the log)

## Later
- [ ] Battle-map images for the four finales
- [ ] Sound: a "music" link per scene to a playlist (the chips already carry the mood words)
- [ ] A printable hero card (the print stylesheet exists; a PDF export would be nicer)
- [ ] The fifth world, written by the family in the series finale
- [ ] Voice: read-aloud text to speech on the deck for when the DM's voice is gone
