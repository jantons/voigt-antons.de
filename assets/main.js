/* voigt-antons.de — shared behaviour: theme, mobile nav, scroll reveal */
(function () {
  'use strict';

  /* ---------- theme ---------- */
  var root = document.documentElement;
  try {
    var saved = localStorage.getItem('theme');
    if (saved === 'dark' || saved === 'light') root.setAttribute('data-theme', saved);
  } catch (e) { /* private mode */ }

  var tt = document.getElementById('themeToggle');
  if (tt) {
    tt.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      root.setAttribute('data-theme', next);
      tt.setAttribute('aria-label', next === 'light' ? 'Switch to dark theme' : 'Switch to light theme');
      try { localStorage.setItem('theme', next); } catch (e) {}
    });
  }

  /* ---------- mobile nav ---------- */
  var nt = document.getElementById('navToggle');
  var mm = document.getElementById('mobileMenu');
  if (nt && mm) {
    nt.addEventListener('click', function () {
      var open = mm.classList.toggle('open');
      nt.setAttribute('aria-expanded', open ? 'true' : 'false');
      nt.textContent = open ? '✕' : '☰';
    });
    mm.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        mm.classList.remove('open');
        nt.setAttribute('aria-expanded', 'false');
        nt.textContent = '☰';
      }
    });
  }

  /* ---------- scroll reveal ---------- */
  var items = document.querySelectorAll('.rv:not(.in)');
  if (!items.length) return;
  if (!('IntersectionObserver' in window)) {
    Array.prototype.forEach.call(items, function (el) { el.classList.add('in'); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
    });
  }, { threshold: 0.1 });
  Array.prototype.forEach.call(items, function (el, i) {
    el.style.transitionDelay = (i % 6) * 45 + 'ms';
    io.observe(el);
  });
})();
