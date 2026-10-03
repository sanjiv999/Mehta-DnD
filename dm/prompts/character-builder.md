# Prompt: build a hero with a player

---
Read CLAUDE.md and characters/GUIDE.md. I am sitting with <PLAYER>, age <AGE>. Walk them through
making a hero. Ask one question at a time in words they can answer. After each answer, offer three
vivid suggestions. When they are happy, write `characters/<id>/character.yaml`, the first journal
entry in their hero's voice, and run `python tools/portrait_prompt.py <id>`. Set `status: active`
and add them to the party in `state/world.yaml`. Validate.
