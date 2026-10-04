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
3. Generate, or paste the prompt into whatever image tool you like and `images.py record` the result.
4. Every generated batch arrives as a pull request. Merging is approval.

## Generating

```bash
export OPENAI_API_KEY=...                      # or STABILITY_API_KEY, or IMAGE_CMD for a local model
python tools/images.py generate --campaign peacock-throne --limit 6 --dry-run
python tools/images.py generate --campaign peacock-throne --limit 6
python tools/images.py heroes                  # portraits for active heroes without one
```

Or in GitHub: Actions → **Generate campaign images** → Run workflow. It needs the API key as a
repository secret and opens a pull request with the pictures.

`IMAGE_CMD` lets you plug in anything: `IMAGE_CMD='python ~/sd/gen.py --prompt {prompt} --out {out}'`.

## Suggested order
Covers (4) → chapter covers (23) → NPCs (~40) → locations (~26) → scenes (~90). A campaign's
first chapter plus its NPCs and places is about fifteen images and makes it feel finished.

## Session recap pictures
After a session, add `image_prompt:` to the session log's front matter describing its best moment,
and the slot `session-NNN` appears in the plan. The Story So Far page becomes an illustrated book.
