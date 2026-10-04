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

## Consistency

Every prompt is assembled the same way:

```
<slot prompt>. <framing for the kind>. Style: <campaign art_style>. <images/STYLE.md notes>. Child-friendly...
```

The campaign's `art_style` is the single source of visual identity, so every image in a world
shares palette and technique, and heroes are drawn in each world's language (the Mughal
miniature in Sikri, the woodblock print on the Moon Road). `images/STYLE.md` is where you add
"all characters keep the same costume colours" and similar continuity notes.

## The human spark

1. `python tools/images.py plan --campaign peacock-throne --missing` lists what is missing with the auto-prompt.
2. For any slot you care about, write a better prompt in `campaigns/<id>/images/overrides.yaml`.
3. Paste the prompt into Gemini or Claude and `images.py intake` the download.
4. Paste, download, `intake`. You chose every picture, so there is nothing to approve.

## Making the pictures (no API key)

```bash
python tools/build_site.py --dm            # then open _site_dm/prompts.html: every prompt with a Copy button
python tools/images.py sheet               # or a Markdown sheet at dm/prompts/PROMPTS.md
python tools/images.py heroes --prompts    # portrait prompts for active heroes
python tools/images.py intake ~/Downloads  # file the downloads by slot name or sheet number
```

Paste each prompt into Gemini or Claude. Save the picture with the slot name (`ch01-s3.png`), or
with the sheet number (`07.png`), or leave the download name and make sure the slot name appears in
it. `intake` files everything, writes sidecars, and records hero portraits. Full walk-through in
`docs/NO-API.md`.

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
