// VGR Contacts — FX layer
(function () {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Footer year
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // ---------- Background video (progressive enhancement) ----------
  // Photo shows first; video only loads on wide screens, fast connections,
  // and when motion is welcome — then crossfades in.
  const video = document.getElementById('fxVideo');
  const media = document.querySelector('.fx-media');
  if (video && media && !reduced && window.innerWidth >= 900) {
    const conn = navigator.connection || {};
    const slow = conn.saveData === true || /2g/.test(conn.effectiveType || '');
    if (!slow) {
      const start = () => {
        video.preload = 'auto';
        video.load();
        video.addEventListener('canplay', () => {
          video.play().then(() => media.classList.add('video-on')).catch(() => {});
        }, { once: true });
      };
      if (document.readyState === 'complete') start();
      else window.addEventListener('load', start);
    }
  }

  // ---------- Particle field ----------
  const canvas = document.getElementById('fxParticles');
  if (canvas && !reduced) {
    const ctx = canvas.getContext('2d');
    let w, h, dpr, particles = [];
    const pointer = { x: -9999, y: -9999 };

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const target = Math.min(110, Math.round((w * h) / 14000));
      particles = Array.from({ length: target }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        r: Math.random() * 1.8 + 0.5,
        vx: (Math.random() - 0.5) * 0.28,
        vy: (Math.random() - 0.5) * 0.28,
        a: Math.random() * 0.5 + 0.2,
        tw: Math.random() * Math.PI * 2
      }));
    }

    function frame() {
      ctx.clearRect(0, 0, w, h);

      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        p.tw += 0.03;

        // gentle repel from pointer
        const dx = p.x - pointer.x, dy = p.y - pointer.y;
        const d2 = dx * dx + dy * dy;
        if (d2 < 16000 && d2 > 0.01) {
          const f = (16000 - d2) / 16000 * 0.9;
          const d = Math.sqrt(d2);
          p.x += (dx / d) * f;
          p.y += (dy / d) * f;
        }

        if (p.x < -20) p.x = w + 20; else if (p.x > w + 20) p.x = -20;
        if (p.y < -20) p.y = h + 20; else if (p.y > h + 20) p.y = -20;

        const alpha = p.a * (0.6 + 0.4 * Math.sin(p.tw));
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(45,191,182,${alpha})`;
        ctx.fill();
      }

      // constellation links
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const a = particles[i], b = particles[j];
          const dx = a.x - b.x, dy = a.y - b.y;
          const d2 = dx * dx + dy * dy;
          if (d2 < 13000) {
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.strokeStyle = `rgba(2,158,151,${(1 - d2 / 13000) * 0.18})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }
      requestAnimationFrame(frame);
    }

    window.addEventListener('resize', resize);
    window.addEventListener('pointermove', e => { pointer.x = e.clientX; pointer.y = e.clientY; });
    window.addEventListener('pointerleave', () => { pointer.x = pointer.y = -9999; });
    resize();
    requestAnimationFrame(frame);
  }

  // ---------- 3D tilt + spotlight ----------
  const fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  if (fine && !reduced) {
    document.querySelectorAll('.ccard').forEach(card => {
      let raf = null, pending = null;

      card.addEventListener('pointermove', e => {
        const r = card.getBoundingClientRect();
        pending = { px: e.clientX - r.left, py: e.clientY - r.top, w: r.width, h: r.height };
        if (raf) return;
        raf = requestAnimationFrame(() => {
          const { px, py, w, h } = pending;
          card.style.setProperty('--mx', px + 'px');
          card.style.setProperty('--my', py + 'px');
          card.style.setProperty('--ry', ((px / w - 0.5) * 13).toFixed(2) + 'deg');
          card.style.setProperty('--rx', ((0.5 - py / h) * 13).toFixed(2) + 'deg');
          raf = null;
        });
      });

      card.addEventListener('pointerleave', () => {
        card.style.setProperty('--rx', '0deg');
        card.style.setProperty('--ry', '0deg');
      });
    });
  }
})();
