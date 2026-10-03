---
title: Crossings (moving heroes between campaigns)
order: 6
---
# Crossings

Heroes are global. Campaigns are worlds. A **Crossing** is how a hero travels from one world
to another when the table switches campaigns.

## How it works

1. The DM runs `python tools/campaign.py switch <id>`.
2. The tool writes a Crossing stub to each party member's journal. Claude or the DM fills it in.
3. The hero keeps: level, abilities, powers, Hero Points, relationships, and one **keepsake** item.
4. The hero's other gear is held in the old world and returns when the party does.
5. The new campaign's `art_style` is used for the next portrait, so the same hero appears
   in the new world's visual language.

## In-fiction explanation

Every campaign has a **Door**: a place where the worlds touch. The Doors are listed in
`campaigns/<id>/campaign.yaml` under `door:`. The common thread across all campaigns is the
**Lantern of Many Roads**, an artifact the party is slowly assembling. Each campaign holds one piece.

## Species and class translation

A hero's species and class stay the same in mechanics but are *described* in the new world's terms.
Example: a Tiger-kin Warrior in The Peacock Throne is a Kitsune Samurai on the Moon Road.
Record the local name under `aliases:` in `character.yaml`.
