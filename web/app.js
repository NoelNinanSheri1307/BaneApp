/**
 * BANE (Biotech Arbitrage Engine) — Web Application Logic
 * Interactive Canvas, Simple Phone Showcase Carousel, Pathfinder Simulator, Diagnostics Modal
 */

(function () {
  'use strict';

  // --------------------------------------------------------------------------
  // 1. SCREENSHOT PROOFS LIST (15 APPSCREENS)
  // --------------------------------------------------------------------------

  const SCREENSHOTS = [
    'proof/Bane (1).png',
    'proof/Bane (2).png',
    'proof/Bane (3).png',
    'proof/Bane (4).png',
    'proof/Bane (5).png',
    'proof/Bane (6).png',
    'proof/Bane (7).png',
    'proof/Bane (8).png',
    'proof/Bane (9).png',
    'proof/Bane (10).png',
    'proof/Bane (11).png',
    'proof/Bane (12).png',
    'proof/Bane (13).png',
    'proof/Bane (14).png',
    'proof/Bane (15).png'
  ];

  const HYPOTHESES = {
    propranolol: {
      step1: { name: 'Propranolol', type: 'Chemical / Non-selective Beta Blocker' },
      step2: { name: 'ADRB2 & VEGF', type: 'Target / Adrenergic & Angiogenesis' },
      step3: { name: 'Endothelial Apoptosis', type: 'Biological Pathway' },
      step4: { name: 'Infantile Hemangioma', type: 'Target Disease Indication' },
      claim: 'Inhibition of beta-2 adrenergic receptors downregulates VEGF/bFGF expression, inducing vasoconstriction and endothelial cell apoptosis in proliferating hemangiomas.',
      metric: '0.94',
      metricLabel: 'Prioritization Score'
    },
    metformin: {
      step1: { name: 'Metformin', type: 'Chemical / Biguanide' },
      step2: { name: 'AMPK / Complex I', type: 'Target / Mitochondrial Metabolism' },
      step3: { name: 'mTORC1 Inhibition', type: 'Cellular Growth Pathway' },
      step4: { name: 'Endometrial Carcinoma', type: 'Target Disease Indication' },
      claim: 'Activation of AMPK by mitochondrial complex I restriction suppresses mTOR signaling, inhibiting tumor cell proliferation and sensitizing insulin-resistant tissue.',
      metric: '0.88',
      metricLabel: 'Prioritization Score'
    },
    thalidomide: {
      step1: { name: 'Thalidomide', type: 'Chemical / Immunomodulatory Drug' },
      step2: { name: 'Cereblon (CRBN)', type: 'Target / E3 Ubiquitin Ligase' },
      step3: { name: 'IKZF1 / IKZF3 Degradation', type: 'Transcription Factor Pathway' },
      step4: { name: 'Multiple Myeloma', type: 'Target Disease Indication' },
      claim: 'Binding to CRBN recruits Ikaros and Aiolos for proteasomal degradation, arresting multiple myeloma cell cycle and modulating cytokine production.',
      metric: '0.96',
      metricLabel: 'Prioritization Score'
    },
    imatinib: {
      step1: { name: 'Imatinib', type: 'Chemical / Tyrosine Kinase Inhibitor' },
      step2: { name: 'PDGFR-β & c-KIT', type: 'Target / Kinase Cascade' },
      step3: { name: 'Fibroblast Proliferation', type: 'Fibrogenesis Pathway' },
      step4: { name: 'Systemic Sclerosis', type: 'Target Disease Indication' },
      claim: 'Dual inhibition of TGF-beta downstream kinases and PDGF receptor phosphorylation attenuates excessive extracellular matrix deposition and myofibroblast activation.',
      metric: '0.82',
      metricLabel: 'Prioritization Score'
    }
  };

  // --------------------------------------------------------------------------
  // 2. BACKGROUND CANVAS PARTICLES (SUBTLE BIOLOGICAL NETWORK)
  // --------------------------------------------------------------------------

  function initBackgroundCanvas() {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let width, height, dpr;
    let particles = [];
    const PARTICLE_COUNT = window.innerWidth < 768 ? 22 : 45;
    const CONNECT_DIST = 140;

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.scale(dpr, dpr);
    }

    function createParticles() {
      particles = [];
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.35,
          vy: (Math.random() - 0.5) * 0.35,
          radius: Math.random() * 1.5 + 0.8,
          isAccent: Math.random() > 0.85
        });
      }
    }

    function render() {
      ctx.clearRect(0, 0, width, height);

      // Draw particle connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < CONNECT_DIST) {
            const alpha = (1 - dist / CONNECT_DIST) * 0.12;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = particles[i].isAccent || particles[j].isAccent
              ? `rgba(224, 122, 56, ${alpha * 1.5})`
              : `rgba(247, 245, 238, ${alpha})`;
            ctx.lineWidth = 0.6;
            ctx.stroke();
          }
        }
      }

      // Draw particle nodes
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = p.isAccent ? 'rgba(224, 122, 56, 0.6)' : 'rgba(247, 245, 238, 0.4)';
        ctx.fill();
      }

      requestAnimationFrame(render);
    }

    window.addEventListener('resize', () => {
      resize();
      createParticles();
    });

    resize();
    createParticles();
    requestAnimationFrame(render);
  }

  // --------------------------------------------------------------------------
  // 3. MOBILE SCREENSHOT SHOWCASE CAROUSEL (CLEAN PHONE FRAME WITH ARROWS)
  // --------------------------------------------------------------------------

  function initScreenshotCarousel() {
    const imgEl = document.getElementById('showcase-img');
    const counterEl = document.getElementById('screen-counter');
    const prevBtn = document.getElementById('carousel-prev');
    const nextBtn = document.getElementById('carousel-next');

    if (!imgEl || !counterEl) return;

    let currentIndex = 0;

    function updateCarousel(index) {
      currentIndex = (index + SCREENSHOTS.length) % SCREENSHOTS.length;
      const src = SCREENSHOTS[currentIndex];
      const displayIndex = String(currentIndex + 1).padStart(2, '0');

      // Smooth fade transition
      imgEl.style.opacity = '0.3';
      setTimeout(() => {
        imgEl.src = src;
        counterEl.textContent = `${displayIndex} / ${String(SCREENSHOTS.length).padStart(2, '0')}`;
        imgEl.style.opacity = '1';
      }, 100);
    }

    function next() {
      updateCarousel(currentIndex + 1);
    }

    function prev() {
      updateCarousel(currentIndex - 1);
    }

    if (prevBtn) prevBtn.addEventListener('click', prev);
    if (nextBtn) nextBtn.addEventListener('click', next);

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight') next();
      if (e.key === 'ArrowLeft') prev();
    });

    // Touch swipe support on phone screen
    let touchStartX = 0;
    imgEl.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    imgEl.addEventListener('touchend', (e) => {
      const touchEndX = e.changedTouches[0].screenX;
      if (touchStartX - touchEndX > 50) next();
      if (touchEndX - touchStartX > 50) prev();
    }, { passive: true });

    updateCarousel(0);
  }

  // --------------------------------------------------------------------------
  // 4. INTERACTIVE PATHFINDER SIMULATOR
  // --------------------------------------------------------------------------

  function initPathfinderSimulator() {
    const buttons = document.querySelectorAll('.hypothesis-btn');
    const node1Name = document.getElementById('node-1-name');
    const node1Type = document.getElementById('node-1-type');
    const node2Name = document.getElementById('node-2-name');
    const node2Type = document.getElementById('node-2-type');
    const node3Name = document.getElementById('node-3-name');
    const node3Type = document.getElementById('node-3-type');
    const node4Name = document.getElementById('node-4-name');
    const node4Type = document.getElementById('node-4-type');
    const claimText = document.getElementById('path-claim-text');
    const metricVal = document.getElementById('path-metric-val');

    if (!buttons.length) return;

    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        buttons.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');

        const key = btn.getAttribute('data-hypothesis');
        const data = HYPOTHESES[key] || HYPOTHESES.propranolol;

        if (node1Name) node1Name.textContent = data.step1.name;
        if (node1Type) node1Type.textContent = data.step1.type;
        if (node2Name) node2Name.textContent = data.step2.name;
        if (node2Type) node2Type.textContent = data.step2.type;
        if (node3Name) node3Name.textContent = data.step3.name;
        if (node3Type) node3Type.textContent = data.step3.type;
        if (node4Name) node4Name.textContent = data.step4.name;
        if (node4Type) node4Type.textContent = data.step4.type;
        if (claimText) claimText.textContent = data.claim;
        if (metricVal) metricVal.textContent = data.metric;
      });
    });
  }

  // --------------------------------------------------------------------------
  // 5. DEMO ENVIRONMENT & LOCAL REPO EXECUTION MODAL
  // --------------------------------------------------------------------------

  function initDemoDiagnosticsModal() {
    const modalBackdrop = document.getElementById('demo-modal');
    const openButtons = document.querySelectorAll('.btn-trigger-demo');
    const closeBtn = document.getElementById('modal-close-btn');

    if (!modalBackdrop) return;

    function openModal() {
      modalBackdrop.classList.add('open');
      document.body.style.overflow = 'hidden';
    }

    function closeModal() {
      modalBackdrop.classList.remove('open');
      document.body.style.overflow = '';
    }

    openButtons.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        openModal();
      });
    });

    if (closeBtn) {
      closeBtn.addEventListener('click', closeModal);
    }

    modalBackdrop.addEventListener('click', (e) => {
      if (e.target === modalBackdrop) {
        closeModal();
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modalBackdrop.classList.contains('open')) {
        closeModal();
      }
    });
  }

  // --------------------------------------------------------------------------
  // 6. INITIALIZE ON DOM READY
  // --------------------------------------------------------------------------

  document.addEventListener('DOMContentLoaded', () => {
    initBackgroundCanvas();
    initScreenshotCarousel();
    initPathfinderSimulator();
    initDemoDiagnosticsModal();
  });
})();
