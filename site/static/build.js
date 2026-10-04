(() => {
  const $ = (s) => document.querySelector(s);
  const pick = (arr, n) => arr.slice().sort(() => Math.random() - 0.5).slice(0, n);
  const SPECIES = ['Human', 'Elf', 'Dwarf', 'Halfling', 'Naga-born', 'Tiger-kin', 'Clockwork', 'Dragonkin', 'Fairy', 'Vanara', 'My own idea'];
  const SPECIES_ICON = { Human: '🧑', Elf: '🧝', Dwarf: '🧔', Halfling: '🧒', 'Naga-born': '🐍', 'Tiger-kin': '🐯', Clockwork: '🤖', Dragonkin: '🐲', Fairy: '🧚', Vanara: '🐒', 'My own idea': '✨' };
  const COOL = [['⚔️', 'Fight with a sword', 'Warrior', 'str'], ['🏹', 'Shoot arrows and track', 'Ranger', 'dex'], ['🤫', 'Sneak and find secrets', 'Rogue', 'dex'], ['✨', 'Do magic', 'Mage', 'int'], ['💚', 'Heal and protect', 'Priest', 'wis'], ['🎵', 'Sing songs that help', 'Bard', 'cha'], ['🐾', 'Talk to animals and change shape', 'Beast-friend', 'wis'], ['🔧', 'Build gadgets', 'Inventor', 'int']];
  const CLASSHP = { Warrior: [10, 'd10'], Ranger: [10, 'd10'], Rogue: [8, 'd8'], Mage: [6, 'd6'], Priest: [8, 'd8'], Bard: [8, 'd8'], 'Beast-friend': [8, 'd8'], Inventor: [8, 'd8'] };
  const CLASSPOWER = { Warrior: 'Shield Friend: when a friend next to me is hit, I take the hit instead (1 per short rest)', Ranger: 'Animal Companion: a loyal creature with 5 HP that does one simple job per turn', Rogue: 'Sneak Attack: +1d6 damage when I attack with advantage or beside a friend', Mage: 'Spark: ranged magic attack 1d8, plus Light, Mend or Message', Priest: 'Healing Touch: heal 1d8 + WIS to a friend', Bard: 'Inspire: give a friend a d6 to add to any roll', 'Beast-friend': 'Wild Shape: become a small animal for a scene (1 per short rest)', Inventor: 'Gadget: one device per long rest that solves a Tricky problem' };
  const SKILLS = ['Athletics', 'Acrobatics', 'Sneaking', 'Tinkering', 'Lore', 'Investigation', 'Nature', 'Animals', 'Perception', 'Medicine', 'Persuasion', 'Performance', 'Bluffing', 'Intimidation'];
  const COLORS = ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'pink', 'gold', 'silver', 'black', 'white', 'rainbow'];
  let tables = { 'hero-seeds': [], 'powers-kids': [], keepsakes: [] };
  fetch('static/tables.json').then(r => r.json()).then(t => { tables = t; }).catch(() => {});
  const H = { player: '', name: '', species: '', cool: null, loves: '', fears: '', dream: '', hair: '', eyes: '', clothes: '', colors: [], special: '', powers: [], keepsake: '', skills: [], home: '', why: '', knows: '', kids: false };

  const steps = [
    { q: 'Who is playing?', render: () => `<input id="f" placeholder="your real name" value="${H.player}"><label class="chk"><input type="checkbox" id="kids" ${H.kids ? 'checked' : ''}> Kids mode (grown-up adds the numbers)</label>`, save: () => { H.player = $('#f').value.trim(); H.kids = $('#kids').checked; } },
    { q: 'If you could be any kind of creature or person in a story, what would you be?', render: () => chips(SPECIES.map(s => [SPECIES_ICON[s], s]), H.species, 'species'), save: () => {} },
    { q: 'What is the coolest thing you can do?', render: () => chips(COOL.map((c, i) => [c[0], c[1], i]), H.cool, 'cool'), save: () => {} },
    { q: 'Who or what do you love most?', render: () => `<input id="f" placeholder="my sister, mangoes, the sea" value="${H.loves}">`, save: () => { H.loves = $('#f').value; } },
    { q: 'What are you a little bit scared of? (it is fine to have nothing)', render: () => `<input id="f" placeholder="thunder, mice, nothing" value="${H.fears}">`, save: () => { H.fears = $('#f').value; } },
    { q: 'What do you want more than anything?', render: () => `<input id="f" placeholder="to fly, to find treasure, to be the bravest" value="${H.dream}">`, save: () => { H.dream = $('#f').value; } },
    { q: 'Here are three hero ideas. Tap one you like, or keep your own.', render: () => { const seeds = pick(tables['hero-seeds'] || [], 3); return seeds.map(s => `<button class="idea" data-v="${s.replace(/"/g, '&quot;')}">${s}</button>`).join('') + `<p class="muted">Picked: <span id="ideapick">${H.idea || 'none yet'}</span></p>`; }, save: () => {} },
    { q: 'What is your hero called?', render: () => `<input id="f" placeholder="a name" value="${H.name}">`, save: () => { H.name = $('#f').value.trim(); } },
    { q: 'What do you look like? Hair, eyes, clothes.', render: () => `<input id="h" placeholder="hair" value="${H.hair}"><input id="e" placeholder="eyes" value="${H.eyes}"><input id="c" placeholder="clothes" value="${H.clothes}">`, save: () => { H.hair = $('#h').value; H.eyes = $('#e').value; H.clothes = $('#c').value; } },
    { q: 'Pick your colours (up to three).', render: () => chips(COLORS.map(c => ['🎨', c]), null, 'colors', true), save: () => {} },
    { q: 'One special detail. A scar, a pet on your shoulder, glowing hands...', render: () => `<input id="f" value="${H.special}">`, save: () => { H.special = $('#f').value; } },
    { q: 'Three powers. Tap ideas or type your own.', render: () => { const ideas = pick(tables['powers-kids'] || [], 4); return ideas.map(s => `<button class="idea pw" data-v="${s.replace(/"/g, '&quot;')}">${s}</button>`).join('') + `<input id="p1" placeholder="power 1" value="${H.powers[0] || ''}"><input id="p2" placeholder="power 2" value="${H.powers[1] || ''}"><input id="p3" placeholder="power 3" value="${H.powers[2] || ''}">`; }, save: () => { H.powers = [$('#p1').value, $('#p2').value, $('#p3').value].filter(Boolean); } },
    { q: 'One treasure you already own. It travels with you between worlds.', render: () => { const ideas = pick(tables.keepsakes || [], 3); return ideas.map(s => `<button class="idea ks" data-v="${s.replace(/"/g, '&quot;')}">${s}</button>`).join('') + `<input id="f" value="${H.keepsake}">`; }, save: () => { H.keepsake = $('#f').value; } },
    { q: 'Four things you are good at.', render: () => chips(SKILLS.map(s => ['⭐', s]), null, 'skills', true), save: () => {} },
    { q: 'Where do you come from? One place, one smell, one sound.', render: () => `<input id="f" value="${H.home}">`, save: () => { H.home = $('#f').value; } },
    { q: 'Why did you leave?', render: () => `<input id="f" placeholder="someone needs help, I got lost, I wanted adventure" value="${H.why}">`, save: () => { H.why = $('#f').value; } },
    { q: 'Who in the party do you already know, and how?', render: () => `<input id="f" value="${H.knows}">`, save: () => { H.knows = $('#f').value; } },
  ];
  function chips(items, current, key, multi) {
    return `<div class="chips">` + items.map(([ic, label, v]) => { const val = v === undefined ? label : v; const on = multi ? (H[key] || []).includes(val) : H[key] === val; return `<button class="chipbtn ${on ? 'on' : ''}" data-key="${key}" data-v="${val}" data-multi="${multi ? 1 : 0}">${ic} ${label}</button>`; }).join('') + `</div>`;
  }
  let i = 0;
  function render() {
    const s = steps[i]; $('#steps').innerHTML = `<h2>${s.q}</h2>${s.render()}`; $('#wpos').textContent = `${i + 1} / ${steps.length}`;
    document.querySelectorAll('.chipbtn').forEach(b => b.addEventListener('click', () => { const k = b.dataset.key, v = isNaN(+b.dataset.v) || b.dataset.v === '' ? b.dataset.v : +b.dataset.v; if (b.dataset.multi === '1') { H[k] = H[k] || []; const idx = H[k].indexOf(v); if (idx >= 0) H[k].splice(idx, 1); else if (H[k].length < (k === 'skills' ? 4 : 3)) H[k].push(v); } else H[k] = v; render(); }));
    document.querySelectorAll('.idea').forEach(b => b.addEventListener('click', () => { if (b.classList.contains('pw')) { const e = ['#p1', '#p2', '#p3'].map(x => $(x)).find(x => !x.value); if (e) e.value = b.dataset.v; } else if (b.classList.contains('ks')) $('#f').value = b.dataset.v; else { H.idea = b.dataset.v; $('#ideapick').textContent = H.idea; } }));
    $('#back').disabled = i === 0; $('#fwd').textContent = i === steps.length - 1 ? 'Finish ✓' : 'Next ▶';
  }
  function finish() {
    const cool = COOL[H.cool || 0]; const cls = cool[2]; const [base, die] = CLASSHP[cls];
    const arr = [15, 14, 13, 12, 10, 8]; const order = [cool[3], ...['str', 'dex', 'con', 'int', 'wis', 'cha'].filter(a => a !== cool[3])];
    const ab = {}; order.forEach((a, k) => ab[a] = arr[k]); const bonus = (v) => Math.floor((v - 10) / 2);
    const hp = base + bonus(ab.con); const ac = 10 + bonus(ab.dex) + (['Warrior', 'Ranger'].includes(cls) ? 1 : 0);
    const id = (H.player || H.name || 'hero').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    const q = (s) => JSON.stringify(String(s || ''));
    const powers = [{ name: cls + ' power', description: CLASSPOWER[cls], uses: 'see class', source: 'class' }, ...H.powers.map(p => ({ name: p, description: p, uses: '1 per short rest', source: 'player' }))];
    const y = `id: ${id}\nplayer: ${q(H.player)}\nname: ${q(H.name)}\nstatus: draft\nkids_mode: ${H.kids}\ncampaign_origin: ${document.body.dataset.active || 'peacock-throne'}\naliases: {}\nconcept: ${q((H.name || 'A hero') + ' the ' + H.species + ' ' + cls + ' who wants ' + (H.dream || 'adventure'))}\nspecies: ${q(H.species)}\nclass: ${q(cls)}\nlevel: 1\nxp: 0\nproficiency: 2\nabilities: { str: ${ab.str}, dex: ${ab.dex}, con: ${ab.con}, int: ${ab.int}, wis: ${ab.wis}, cha: ${ab.cha} }\nhp: { max: ${hp}, current: ${hp} }\nac: ${ac}\nspeed: 30\nhero_points: 3\nhit_dice: ${die}\ntrained_skills: [${(H.skills || []).join(', ')}]\npowers:\n${powers.map(p => `  - { name: ${q(p.name)}, kid_name: "", description: ${q(p.description)}, uses: ${q(p.uses)}, source: ${p.source} }`).join('\n')}\ninventory:\n  - { name: "Adventurer's pack", qty: 1, notes: "rope, torch, rations x3" }\nkeepsake: ${q(H.keepsake)}\ncoins: 10\nappearance: { age: "", height: "", build: "", hair: ${q(H.hair)}, eyes: ${q(H.eyes)}, skin: "", clothing: ${q(H.clothes)}, distinguishing: ${q(H.special)}, colors: ${q((H.colors || []).join(', '))} }\npersonality: { traits: [], loves: [${(H.loves || '').split(',').map(s => q(s.trim())).filter(s => s !== '""').join(', ')}], fears: [${(H.fears || '').split(',').map(s => q(s.trim())).filter(s => s !== '""').join(', ')}], dream: ${q(H.dream)}, ideal: "", bond: "", flaw: "" }\nbackstory: ${q([H.home, H.why, H.knows].filter(Boolean).join(' '))}\ncompanions: []\nrelationships: []\nconditions: []\nachievements: []\nportrait: { style_override: "", current: "", history: [] }\nsecret: ""\n`;
    $('#yaml').textContent = y; $('#summary').innerHTML = `<h3>${H.name || 'Unnamed'}</h3><p>${H.species} ${cls} · HP ${hp} · AC ${ac}</p><p>${H.idea ? 'Idea: ' + H.idea : ''}</p><p>Powers: ${powers.map(p => p.name).join(', ')}</p><p>Keepsake: ${H.keepsake || '-'}</p>`;
    $('#steps').hidden = true; document.querySelector('.decknav').hidden = true; $('#result').hidden = false;
    $('#copyclaude').onclick = async () => { const msg = `Please add this hero to the game (from the website's hero builder). Check the numbers against the rules, write the first journal entry with me, and give me the portrait prompt.\n\n\`\`\`yaml\n${y}\`\`\``; try { await navigator.clipboard.writeText(msg); } catch (e) { const ta = document.createElement('textarea'); ta.value = msg; document.body.append(ta); ta.select(); document.execCommand('copy'); ta.remove(); } $('#copied').textContent = 'Copied. Paste it into the chat with Claude.'; };
    $('#download').onclick = () => { const b = new Blob([y], { type: 'text/yaml' }); const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = 'character.yaml'; a.click(); };
  }
  $('#fwd').addEventListener('click', () => { steps[i].save(); if (i === steps.length - 1) finish(); else { i++; render(); } });
  $('#back').addEventListener('click', () => { steps[i].save(); i = Math.max(0, i - 1); render(); });
  render();
})();
