document.addEventListener('DOMContentLoaded', () => {
  // Animate hero text fade-in
  const hero = document.querySelector('.home-hero');
  if (hero) {
    hero.classList.add('opacity-100','translate-y-0');
  }

  // Simple fade-up for project cards
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('opacity-100','translate-y-0');
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.2 });

  document.querySelectorAll('[data-animate]').forEach(el => observer.observe(el));
});