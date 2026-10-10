# Images: how pictures get made and kept consistent

The site is designed to look complete at every stage. Every place a picture can go is an
**image slot**, and every slot has a composed prompt. Until a real image exists, the build
renders a procedural placeholder in the campaign's colours, so nothing is ever blank.

## Slots

| Slot | Where it shows | Prompt source |
|---|---|---|
| `cover` | campaign card and header | `campaign.yaml: cover_prompt` |
| `map` | map tab background | `campaign.yaml: map.prompt` (or a default) |
| `chNN` | chapter row and deck title slide | chapter front matter `image_prompt` |
| `chNN-sN` | scene slide | the scene's `- **Image:**` line, else its read-aloud text |
| `npc-<slug>` | People tab card | NPC front matter `image_prompt`, else its **Looks** line |
| `loc-<slug>` | Places tab card and map marker | location front matter `image_prompt`, else **First impression** |
| hero portraits | hero page and party cards | `tools/portrait_prompt.py` from the sheet |
| `session-NNN` | Story So Far and session log | the session's `image_prompt` front matter (optional) |

Files live at `campaigns/<id>/images/<slot>.png` (or .jpg/.webp/.svg). A sidecar
`<slot>.yaml` records the prompt, provider and date. **Player art** at `campaigns/<id>/art/<slot>.png`
always wins: scan the kids' drawings and they replace the generated picture.

## Consistency: how a face stays the same for sixty hours

Image models have no memory between pictures. The only persistence is in the words, and in
reference pictures. Every prompt is therefore built in the same layers, in the same order:

```
Style: <the world's art_style>  <images/STYLE.md: palette, light, line, nevers>
Moment: <the scene's Image line>
Who is in it, drawn exactly like this: <Name: canon look>. <Name: canon look>.
Where: <Place: what you see first>. Time of day: <its hour>.
Match the attached reference pictures for <names>.
<framing for the kind, with the aspect ratio>  <rules: one style, no text, child-friendly>
```

- **Style anchor.** `campaign.yaml: art_style` names the medium; `images/STYLE.md` is the art
  bible: a named palette, the light, the line, what the world never shows. Both go first in every
  prompt so the model keys on them before anything else.
- **Canon looks.** A character's **Looks** line in `npcs/<slug>.md` is the one description of
  that character. Any scene whose read-aloud, jobs or Image line names them gets that sentence
  verbatim. Change the line and every later picture follows. Heroes use `appearance` from their
  sheet (or `portrait.canon`, one pinned sentence), so a hero looks the same in a portrait, a
  scene and another world.
- **Canon places.** A location's **First seen** and **Hour** lines do the same for buildings and
  light.
- **References.** Once a character or place has a picture, every later prompt that includes them
  says to attach it. Gemini and Claude both accept reference pictures; this is the strongest
  consistency tool there is. Make the people and places before the scenes they appear in, which
  is the order `PICTURES.md` uses.
- **Numbers never move.** `dm/prompts/sheet.json` gives every picture a number for life, so
  `07.png` means the same picture whenever it is uploaded.

## Fight and payoff pictures

A scene's `- **Image:**` line is its opening picture. Every fight or climax also has
`- **Image (after):**`, the payoff (slot `chNN-sN-after`), and a scene that turns into a fight
halfway has `- **Image (fight):**` (slot `chNN-sN-fight`). They get numbers in `PICTURES.md` like any
other picture. On the kids' slides the fight picture shows as soon as it exists; the payoff stays
hidden until the fight is won (Claude adds the slot to `flags.revealed_images` in `state.yaml`) or
the chapter is over. The validator refuses a fight without a payoff picture.

## The one list

`python tools/images.py pictures` writes `PICTURES.md` at the top of the repo: the active world's
current chapter first (cover, chapter opener, scenes in order), then the people and places that
chapter mentions, then hero portraits, then everything else in order of need, then what is done.
`session.py prep` repeats the current chapter's part of it. The site's DM screen renders the same
prompts with copy buttons.

## Getting pictures in

| Route | How |
|---|---|
| `inbox/` on GitHub | Upload with the number or slot name; the intake workflow files it, refreshes the list and rebuilds the site |
| The chat | Paste the pictures and say the numbers; Claude runs `images.py intake <folder> --assign 07,12,13` |
| Any folder | `python tools/images.py intake ~/Downloads --move` |

Player art at `campaigns/<id>/art/<slot>.png` always wins over generated art.

## Optional: letting an API do the pasting

`images.py generate --provider openai|stability|cmd` and the **Generate campaign images** workflow
exist for anyone who prefers to pay per image. They never run unless started by hand.
`IMAGE_CMD` lets you plug in a local model: `IMAGE_CMD='python ~/sd/gen.py --prompt {prompt} --out {out}'`.

## Suggested order
Covers (4) → chapter covers (23) → NPCs (~40) → locations (~26) → scenes (~90). A campaign's
first chapter plus its NPCs and places is about fifteen images and makes it feel finished.

## Session recap pictures
After a session, add `image_prompt:` to the session log's front matter describing its best moment,
and the slot `session-NNN` appears in the plan. The Story So Far page becomes an illustrated book.
