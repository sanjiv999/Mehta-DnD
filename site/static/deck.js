(() => {
  const slides = [...document.querySelectorAll('.slide')]; let i = 0;
  const pos = document.getElementById('pos');
  const show = (n) => { i = Math.max(0, Math.min(slides.length - 1, n)); slides.forEach((s, k) => s.classList.toggle('active', k === i)); pos.textContent = `${i + 1} / ${slides.length}`; window.scrollTo({ top: 0 }); try { localStorage.setItem('deck:' + location.pathname, i); } catch (e) {} };
  document.getElementById('prev').addEventListener('click', () => show(i - 1));
  document.getElementById('next').addEventListener('click', () => show(i + 1));
  document.addEventListener('keydown', (e) => { if (e.key === 'ArrowRight' || e.key === ' ') show(i + 1); if (e.key === 'ArrowLeft') show(i - 1); });
  document.querySelectorAll('.choice').forEach(b => b.addEventListener('click', () => { b.parentElement.querySelectorAll('.choice').forEach(x => x.classList.remove('picked')); b.classList.add('picked'); }));
  let x0 = null; document.addEventListener('touchstart', e => { x0 = e.touches[0].clientX; }); document.addEventListener('touchend', e => { if (x0 == null) return; const dx = e.changedTouches[0].clientX - x0; if (Math.abs(dx) > 60) show(i + (dx < 0 ? 1 : -1)); x0 = null; });
  try { const saved = +localStorage.getItem('deck:' + location.pathname); if (saved) show(saved); } catch (e) {}
})();
