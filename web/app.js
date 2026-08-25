/**
 * BANE (Biotech Arbitrage Engine) — Web Application Logic
 * Interactive Canvas, Smartphone Showcase Carousel, Swanson ABC Simulator, Diagnostics Modal
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

  // Swanson ABC Repurposing Model & Signal Score Breakdown Data
  const SWANSON_MODELS = {
    indirect_abc: {
      step1: { name: 'Node A: Existing Drug', type: 'Approved Molecule / Chemical Entity' },
      step2: { name: 'Node B: Biological Target', type: 'Gene / Protein / Enzyme Bridge' },
      step3: { name: 'Node C: Target Disease', type: 'Secondary Disease Indication' },
      step4: { name: 'Repurposing Signal (A → C)', type: 'Transitive Hypothesis Dossier' },
      arrow1: 'INHIBITS / MODULATES',
      arrow2: 'CAUSES / DRIVES',
      arrow3: 'EMERGENT LINK',
      claim: "Swanson's A → B → C Model: If Drug A modulates Target B, and Target B is a causal driver in Disease C, an indirect repurposing signal (A → C) is inferred and scored across literature citations.",
      signalScore: '89',
      mechVal: '92%',
      clinVal: '86%',
      litVal: '85%',
      novVal: '94%'
    },
    direct_baseline: {
      step1: { name: 'Node A: Existing Drug', type: 'Known Pharmaceutical Compound' },
      step2: { name: 'Published Literature Corpus', type: 'Europe PMC / PubMed Index' },
      step3: { name: 'Primary Indication C', type: 'Established Therapeutic Use' },
      step4: { name: 'Baseline Control Profile', type: 'Direct Association Benchmark' },
      arrow1: 'INDEXED IN',
      arrow2: 'REPORTED FOR',
      arrow3: 'BENCHMARKED',
      claim: 'Direct Literature Baseline: Evaluates well-established primary indications to benchmark novel candidate signals and isolate genuine secondary repurposing opportunities from prior art.',
      signalScore: '74',
      mechVal: '88%',
      clinVal: '90%',
      litVal: '92%',
      novVal: '25%'
    },
    shared_cascade: {
      step1: { name: 'Node A: Multi-Target Drug', type: 'Kinase / Small Molecule Inhibitor' },
      step2: { name: 'Upstream Target B1', type: 'Cell Surface Receptor / Kinase' },
      step3: { name: 'Pathway Node B2', type: 'Downstream Signaling Cascade' },
      step4: { name: 'Complex Indication C', type: 'Multi-Step Pathway Repurposing' },
      arrow1: 'BINDS TO',
      arrow2: 'SIGNAL CASCADE',
      arrow3: 'MODULATES',
      claim: 'Multi-Hop Pathway Cascades: Resolves multi-protein biological cascades where initial target inhibition propagates downstream to reverse pathological disease mechanisms.',
      signalScore: '83',
      mechVal: '85%',
      clinVal: '80%',
      litVal: '81%',
      novVal: '88%'
    },
    target_reversal: {
      step1: { name: 'Node A: Target Antagonist', type: 'Competitive / Allosteric Inhibitor' },
      step2: { name: 'Overexpressed Target B', type: 'Oncogenic / Inflammatory Protein' },
      step3: { name: 'Pathological Phenotype', type: 'Hyperactive Disease Pathway' },
      step4: { name: 'High-Impact Candidate', type: 'Target-Reversal Repurposing' },
      arrow1: 'DOWNREGULATES',
      arrow2: 'PATHOLOGY DRIVER',
      arrow3: 'REVERSAL SIGNAL',
      claim: 'Phenotypic Target Reversal: Identifies drugs capable of downregulating proteins that are abnormally overexpressed or hyperactive in disease tissues.',
      signalScore: '93',
      mechVal: '96%',
      clinVal: '91%',
      litVal: '89%',
      novVal: '95%'
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
  // 3. MOBILE SCREENSHOT SHOWCASE CAROUSEL (SMARTPHONE FRAME WITH ARROWS)
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
  // 4. SWANSON ABC MODEL & SIGNAL SCORE SIMULATOR
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
    const arrow1Text = document.getElementById('arrow-1-text');
    const arrow2Text = document.getElementById('arrow-2-text');
    const arrow3Text = document.getElementById('arrow-3-text');
    const claimText = document.getElementById('path-claim-text');
    const metricVal = document.getElementById('path-metric-val');

    const barMech = document.getElementById('bar-mech');
    const barClin = document.getElementById('bar-clin');
    const barLit = document.getElementById('bar-lit');
    const barNov = document.getElementById('bar-nov');

    if (!buttons.length) return;

    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        buttons.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');

        const key = btn.getAttribute('data-model');
        const data = SWANSON_MODELS[key] || SWANSON_MODELS.indirect_abc;

        if (node1Name) node1Name.textContent = data.step1.name;
        if (node1Type) node1Type.textContent = data.step1.type;
        if (node2Name) node2Name.textContent = data.step2.name;
        if (node2Type) node2Type.textContent = data.step2.type;
        if (node3Name) node3Name.textContent = data.step3.name;
        if (node3Type) node3Type.textContent = data.step3.type;
        if (node4Name) node4Name.textContent = data.step4.name;
        if (node4Type) node4Type.textContent = data.step4.type;

        if (arrow1Text) arrow1Text.textContent = data.arrow1;
        if (arrow2Text) arrow2Text.textContent = data.arrow2;
        if (arrow3Text) arrow3Text.textContent = data.arrow3;

        if (claimText) claimText.textContent = data.claim;
        if (metricVal) metricVal.textContent = data.signalScore;

        if (barMech) barMech.style.width = data.mechVal;
        if (barClin) barClin.style.width = data.clinVal;
        if (barLit) barLit.style.width = data.litVal;
        if (barNov) barNov.style.width = data.novVal;
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
