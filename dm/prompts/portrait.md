# Prompt: hero portrait

`python tools/portrait_prompt.py <id>` assembles this automatically from `character.yaml` and
the active campaign's `art_style`. The structure is:

```
Portrait of <name>, a <age> <species> <class>. <appearance sentences>.
Holding or wearing: <keepsake and signature gear>. Expression: <personality in one phrase>.
Companion: <companion if any>. Setting: <current location, one phrase>.
Style: <campaign art_style>. Composition: waist-up, centered, looking slightly past the viewer,
clean background with ornamental border, no text, no watermark. Child-friendly, no weapons
pointed at the viewer.
```

Save the result to `characters/<id>/portraits/NNN.png` and record it:

```bash
python tools/portrait_prompt.py <id> --record NNN.png --session <N> --note "after the baoli"
```
