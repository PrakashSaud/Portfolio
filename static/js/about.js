document.addEventListener('DOMContentLoaded', () => {
  // Reveal-on-scroll + skill fill
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      e.target.classList.add('opacity-100','translate-y-0');
      e.target.querySelectorAll('.skill-fill').forEach(bar => {
        const lvl = Math.max(0, Math.min(100, parseInt(bar.dataset.level || '0', 10)));
        bar.style.width = lvl + '%';
      });
      io.unobserve(e.target);
    });
  }, { threshold: 0.2 });

  document.querySelectorAll('[data-animate]').forEach(el => {
    io.observe(el);
  });
});