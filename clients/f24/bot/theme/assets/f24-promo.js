/* F24 Promo · countdown + reveal + calc · self-contained, idempotent */
(function () {
  if (window.__f24PromoBooted) return;
  window.__f24PromoBooted = true;

  function boot() { _f24PromoBoot(); }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();

function _f24PromoBoot() {
  // Safety fallback: si por cualquier razón el reveal no dispara,
  // forzamos visible en 150ms para que NUNCA quede en blanco.
  setTimeout(function () {
    document.querySelectorAll('.f24p-rev:not(.is-in)').forEach(function (el) {
      el.classList.add('is-in');
    });
  }, 1500);

  // ---------- Countdown ----------
  function pad(n) { return String(n).padStart(2, '0'); }
  function tick() {
    var nodes = document.querySelectorAll('[data-countdown-end]');
    if (!nodes.length) return;
    var now = Date.now();
    nodes.forEach(function (n) {
      var endIso = n.getAttribute('data-countdown-end');
      var end = Date.parse(endIso);
      if (isNaN(end)) return;
      var diff = end - now;
      if (diff <= 0) {
        n.setAttribute('data-expired', '1');
        diff = 0;
      }
      var d = Math.floor(diff / 86400000);
      var h = Math.floor((diff % 86400000) / 3600000);
      var m = Math.floor((diff % 3600000) / 60000);
      var s = Math.floor((diff % 60000) / 1000);
      var qd = n.querySelector('[data-cd-d]');
      var qh = n.querySelector('[data-cd-h]');
      var qm = n.querySelector('[data-cd-m]');
      var qs = n.querySelector('[data-cd-s]');
      var ql = n.querySelector('[data-cd-line]');
      if (qd) qd.textContent = pad(d);
      if (qh) qh.textContent = pad(h);
      if (qm) qm.textContent = pad(m);
      if (qs) qs.textContent = pad(s);
      if (ql) {
        if (diff <= 0) {
          ql.textContent = 'Promoción finalizada — pregunta por la vigente.';
        } else if (d >= 1) {
          ql.textContent = d + (d === 1 ? ' día' : ' días') + ' · ' + pad(h) + ':' + pad(m) + ':' + pad(s);
        } else {
          ql.textContent = pad(h) + ':' + pad(m) + ':' + pad(s) + ' restantes';
        }
      }
    });
  }
  tick();
  setInterval(tick, 1000);

  // ---------- Reveal-on-scroll ----------
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('is-in');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    document.querySelectorAll('.f24p-rev').forEach(function (el) { io.observe(el); });
  } else {
    document.querySelectorAll('.f24p-rev').forEach(function (el) { el.classList.add('is-in'); });
  }

  // ---------- MSI Calculator ----------
  document.querySelectorAll('[data-msi-calc]').forEach(function (root) {
    var sel = root.querySelector('[data-msi-product]');
    var out3 = root.querySelector('[data-msi-3]');
    var out6 = root.querySelector('[data-msi-6]');
    var out9 = root.querySelector('[data-msi-9]');
    var price = root.querySelector('[data-msi-price]');
    var img = root.querySelector('[data-msi-img]');
    var name = root.querySelector('[data-msi-name]');
    var wa = root.querySelector('[data-msi-wa]');
    var waBase = root.getAttribute('data-msi-wa-base') || 'https://wa.me/523317903630';
    function fmt(n) {
      return '$' + Math.round(n).toLocaleString('es-MX');
    }
    function update() {
      if (!sel) return;
      var opt = sel.options[sel.selectedIndex];
      if (!opt) return;
      var p = parseFloat(opt.getAttribute('data-price') || '0');
      if (!isFinite(p) || p <= 0) return;
      if (price) price.textContent = fmt(p);
      if (out3) out3.textContent = fmt(p / 3) + ' /mes';
      if (out6) out6.textContent = fmt(p / 6) + ' /mes';
      if (out9) out9.textContent = fmt(p / 9) + ' /mes';
      // Meses MSI reales del producto (data-msi ← metafield f24.msi_meses ← sheet).
      var ladder = (opt.getAttribute('data-msi') || '3,6').split(',')
        .map(Number).filter(function (n) { return n > 0; });
      var maxM = ladder.length ? ladder[ladder.length - 1] : 6;
      [3, 6, 9, 12].forEach(function (m) {
        var row = root.querySelector('[data-msi-row="' + m + '"]');
        if (!row) return;
        var on = ladder.indexOf(m) !== -1;
        row.style.display = on ? '' : 'none';
        row.classList.toggle('f24p-calc__option--best', on && m === maxM && ladder.length > 1);
        var amt = row.querySelector('[data-msi-amt]');
        if (amt) amt.textContent = fmt(p / m) + ' /mes';
      });
      var ctaMax = root.querySelector('[data-msi-cta-max]');
      if (ctaMax) ctaMax.textContent = maxM;
      if (img) {
        var src = opt.getAttribute('data-img');
        if (src) img.setAttribute('src', src);
      }
      if (name) name.textContent = opt.textContent;
      if (wa) {
        var title = opt.textContent;
        var sku = opt.getAttribute('data-sku') || '';
        var msg = 'Hola Ferre24, quiero ' + title + ' (' + sku + ') a ' + maxM + ' MSI sin intereses. ¿Me cotizan?';
        wa.setAttribute('href', waBase + '?text=' + encodeURIComponent(msg));
      }
    }
    if (sel) sel.addEventListener('change', update);
    update();
  });

  // ---------- Sticky bar dismiss ----------
  document.querySelectorAll('[data-promo-bar-close]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var bar = btn.closest('[data-promo-bar]');
      if (bar) bar.style.display = 'none';
      try { sessionStorage.setItem('f24_promo_bar_closed', '1'); } catch (e) {}
    });
  });
  try {
    if (sessionStorage.getItem('f24_promo_bar_closed')) {
      document.querySelectorAll('[data-promo-bar]').forEach(function (b) { b.style.display = 'none'; });
    }
  } catch (e) {}
}


/* F24_PROMO_CLICWA - Fase 2d: promociones no carga f24-maq.js -> sus botones [data-wa] no
   disparaban ClicWhatsApp. GUARD de registro unico: f24-promo.js se incluye VARIAS veces en
   esta pagina, sin el guard el evento se dispararia N veces por click (doble-conteo). */
(function () {
  try {
    if (window.__F24_PROMO_WA) return;
    window.__F24_PROMO_WA = true;
    function fireWA(group, ctaText) {
      var p = { source: "landing-promociones", group: group || "promo", cta: ctaText || "" };
      try { window.fbq && fbq("trackCustom", "ClicWhatsApp", p); } catch (e) {}
      try { window.gtag && gtag("event", "clic_whatsapp", p); } catch (e) {}
      try { (window.dataLayer = window.dataLayer || []).push(Object.assign({ event: "clic_whatsapp" }, p)); } catch (e) {}
    }
    document.addEventListener("click", function (ev) {
      var a = ev.target && ev.target.closest && ev.target.closest("[data-wa], a[href*='wa.me'], a[href*='whatsapp.com']");
      if (a) fireWA(a.getAttribute && a.getAttribute("data-wa-group"), (a.textContent || "").trim().slice(0, 60));
    }, true);
  } catch (e) {}
})();
