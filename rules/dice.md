---
title: Dice and Oracles
order: 5
---
# Dice and Oracles

## Dice notation

`NdS+M`: roll N dice with S sides and add M. Examples: `d20`, `2d6+3`, `4d6kh3` (keep highest three).

```bash
python tools/roll.py d20 --adv        # advantage
python tools/roll.py 2d6+3 --label "Arya's talwar"
python tools/roll.py 4d6kh3 -n 6      # roll ability scores
python tools/roll.py --table weather
python tools/roll.py --oracle likely   # yes/no with a nudge
```

Every roll is appended to `dm/rolls.log` with a timestamp and label. The website's `dice.html`
has the same roller for phones.

## The Oracle

When the DM does not know what happens, ask the oracle a yes/no question and give it a likelihood.

| Likelihood | Yes on d20 |
|---|---|
| Almost certain | 3+ |
| Likely | 7+ |
| Even | 11+ |
| Unlikely | 15+ |
| Almost impossible | 19+ |

A roll within 2 of the threshold gives "yes, but" or "no, but". A natural 20 or 1 adds a twist from `dm/tables/twists.yaml`.

## Tables

Tables live in `dm/tables/*.yaml`:

```yaml
name: weather
die: d8
entries:
  - Clear and hot
  - { text: "Sudden monsoon shower", weight: 2 }
```
