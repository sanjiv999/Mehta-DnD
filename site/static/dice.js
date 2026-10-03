(() => {
  const $ = (s) => document.querySelector(s);
  const log = $('#log'); const total = $('#total'); const detail = $('#detail'); const result = $('#result');
  let dc = null;
  const rnd = (n) => 1 + Math.floor(Math.random() * n);
  const TWISTS = ["An old friend appears, in trouble.", "It was here all along, in plain sight.", "An animal arrives with a message.",
    "The villain's helper has a change of heart.", "The weather turns.", "A door opens that should not exist.",
    "Someone laughs, and it was the wrong person.", "The ground gives way to somewhere wonderful.",
    "A child asks for help.", "A keepsake glows.", "The enemy is also lost.", "Music, from nowhere."];

  function save(line) {
    const li = document.createElement('li'); li.textContent = line; log.prepend(li);
    try { const a = JSON.parse(localStorage.getItem('rolls') || '[]'); a.unshift(line); localStorage.setItem('rolls', JSON.stringify(a.slice(0, 200))); } catch (e) {}
  }
  function show(t, d, cls) {
    total.textContent = t; detail.textContent = d; result.className = 'result ' + (cls || '');
    result.animate([{ transform: 'scale(1.15)' }, { transform: 'scale(1)' }], { duration: 250 });
  }
  function who() { const w = $('#who').value.trim(); return w ? w + ' ' : ''; }

  function rollExpr(expr) {
    const m = expr.replace(/\s/g, '').match(/^(\d*)d(\d+)(?:k([hl])(\d+))?([+-]\d+)?$/i);
    if (!m) return null;
    const n = +(m[1] || 1), sides = +m[2], mod = +(m[5] || 0);
    let rolls = Array.from({ length: n }, () => rnd(sides)), kept = rolls;
    if (m[3]) kept = [...rolls].sort((a, b) => m[3].toLowerCase() === 'h' ? b - a : a - b).slice(0, +m[4]);
    const sum = kept.reduce((a, b) => a + b, 0) + mod;
    return { sum, text: `[${rolls.join(', ')}]${m[3] ? ' keep [' + kept.join(', ') + ']' : ''}${mod ? (mod > 0 ? ' +' : ' ') + mod : ''}` };
  }

  function rollDie(sides) {
    const mod = +($('#mod').value || 0);
    const adv = $('#adv').checked, dis = $('#dis').checked;
    let r, text, nat;
    if (sides === 20 && adv !== dis) {
      const a = rnd(20), b = rnd(20); nat = adv ? Math.max(a, b) : Math.min(a, b);
      text = `[${a}, ${b}] ${adv ? 'advantage' : 'disadvantage'} → ${nat}`;
    } else { nat = rnd(sides); text = `[${nat}]`; }
    r = nat + mod; if (mod) text += (mod > 0 ? ' +' : ' ') + mod;
    let cls = '', tag = '';
    if (sides === 20 && nat === 20) { cls = 'big'; tag = ' BIG WIN!'; }
    else if (sides === 20 && nat === 1) { cls = 'whoops'; tag = ' Whoops!'; }
    else if (sides === 20 && dc != null) { cls = r >= dc ? 'ok' : 'fail'; tag = r >= dc ? ` ✓ beats ${dc}` : ` ✗ needs ${dc}`; }
    show(r, text + tag, cls);
    save(`${who()}d${sides}${mod ? (mod > 0 ? '+' : '') + mod : ''} = ${r}  ${text}${tag}`);
  }

  document.querySelectorAll('.die').forEach(b => b.addEventListener('click', () => rollDie(+b.dataset.die)));
  document.querySelectorAll('.dc').forEach(b => b.addEventListener('click', () => {
    const on = b.classList.contains('on'); document.querySelectorAll('.dc').forEach(x => x.classList.remove('on'));
    dc = on ? null : +b.dataset.dc; if (!on) b.classList.add('on');
  }));
  $('#adv').addEventListener('change', e => { if (e.target.checked) $('#dis').checked = false; });
  $('#dis').addEventListener('change', e => { if (e.target.checked) $('#adv').checked = false; });
  const go = () => { const r = rollExpr($('#expr').value); if (!r) { show('?', 'try 2d6+3'); return; } show(r.sum, r.text); save(`${who()}${$('#expr').value} = ${r.sum}  ${r.text}`); };
  $('#go').addEventListener('click', go); $('#expr').addEventListener('keydown', e => { if (e.key === 'Enter') go(); });

  document.querySelectorAll('.oracle').forEach(b => b.addEventListener('click', () => {
    const thr = +b.dataset.thr, r = rnd(20); let a;
    if (r === 20) a = 'YES, and something better'; else if (r === 1) a = 'NO, and something worse';
    else if (r >= thr) a = r - thr < 2 ? 'Yes, but…' : 'Yes'; else a = thr - r <= 2 ? 'No, but…' : 'No';
    let t = `${a} (rolled ${r}, needed ${thr}+)`;
    if (r === 1 || r === 20) t += ' · Twist: ' + TWISTS[rnd(TWISTS.length) - 1];
    $('#oracle-result').textContent = t; save(`Oracle (${b.textContent}): ${t}`);
  }));
  $('#clear').addEventListener('click', () => { log.innerHTML = ''; try { localStorage.removeItem('rolls'); } catch (e) {} });
  try { JSON.parse(localStorage.getItem('rolls') || '[]').forEach(l => { const li = document.createElement('li'); li.textContent = l; log.append(li); }); } catch (e) {}
})();
