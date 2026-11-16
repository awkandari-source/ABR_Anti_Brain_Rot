/* ==========================================================================
   ABR Anti-Brain Rot — Interactive Bedtime Companion & Playlist Filter
   100% Zero-Audio / Zero-Music Browser Utility (Safe for Quiet Bedrooms)
   ========================================================================== */

(function () {
  const STORAGE_KEY = 'abr_evening_winddown_v1';

  const items = Array.from(document.querySelectorAll('.winddown-item'));
  const progressEl = document.getElementById('winddown-progress');
  const resetBtn = document.getElementById('winddown-reset');

  function loadState() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    } catch (_) {
      return {};
    }
  }

  function saveState(state) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (_) {}
  }

  function updateChecklistUI() {
    const state = loadState();
    let doneCount = 0;
    items.forEach((item) => {
      const stepId = item.getAttribute('data-step');
      const cb = item.querySelector('input[type="checkbox"]');
      const checked = Boolean(state[stepId]);
      cb.checked = checked;
      item.classList.toggle('completed', checked);
      if (checked) doneCount += 1;
    });
    if (progressEl) {
      progressEl.textContent =
        doneCount === items.length
          ? 'All 5 Golden-Hour steps complete — wishing your household a peaceful, zero-music rest.'
          : `${doneCount} of ${items.length} evening wind-down steps checked tonight.`;
    }
  }

  items.forEach((item) => {
    const cb = item.querySelector('input[type="checkbox"]');
    item.addEventListener('click', (e) => {
      if (e.target !== cb) {
        cb.checked = !cb.checked;
      }
      const state = loadState();
      state[item.getAttribute('data-step')] = cb.checked;
      saveState(state);
      updateChecklistUI();
    });
  });

  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      saveState({});
      updateChecklistUI();
    });
  }

  updateChecklistUI();

  // Silent Visual 3-Breath Bedtime Anchor (4s Inhale / 6s Exhale x 3 rounds)
  const breathBtn = document.getElementById('breath-start-btn');
  const breathOrb = document.getElementById('breath-orb');
  const breathStatus = document.getElementById('breath-status');
  let breathTimers = [];
  let running = false;

  function clearBreathTimers() {
    breathTimers.forEach((t) => clearTimeout(t));
    breathTimers = [];
  }

  function stopBreathing(message) {
    clearBreathTimers();
    running = false;
    if (breathOrb) {
      breathOrb.classList.remove('inhale', 'exhale');
      breathOrb.textContent = '4s · 6s';
    }
    if (breathStatus) {
      breathStatus.textContent = message || 'Silent visual pacer · 0% sound';
    }
    if (breathBtn) {
      breathBtn.textContent = 'Start 3 Slow Belly Breaths';
    }
  }

  if (breathBtn && breathOrb && breathStatus) {
    breathBtn.addEventListener('click', () => {
      if (running) {
        stopBreathing('Paused · Ready whenever you are');
        return;
      }
      running = true;
      breathBtn.textContent = 'Stop Pacer';
      const totalRounds = 3;

      for (let round = 0; round < totalRounds; round += 1) {
        const offset = round * 10000;
        breathTimers.push(
          setTimeout(() => {
            breathOrb.classList.remove('exhale');
            breathOrb.classList.add('inhale');
            breathOrb.textContent = 'Inhale';
            breathStatus.textContent = `Breath ${round + 1} of ${totalRounds} · Smell the wildflower (4 seconds)…`;
          }, offset + 50)
        );
        breathTimers.push(
          setTimeout(() => {
            breathOrb.classList.remove('inhale');
            breathOrb.classList.add('exhale');
            breathOrb.textContent = 'Exhale';
            breathStatus.textContent = `Breath ${round + 1} of ${totalRounds} · Blow the dandelion softly (6 seconds)…`;
          }, offset + 4050)
        );
      }

      breathTimers.push(
        setTimeout(() => {
          stopBreathing('3 calm breaths complete · Ready for lights-out');
        }, totalRounds * 10000 + 100)
      );
    });
  }

  // Playlist Category Filter
  const tabs = Array.from(document.querySelectorAll('.filter-tab'));
  const cards = Array.from(document.querySelectorAll('.playlist-card'));

  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      const cat = tab.getAttribute('data-filter');
      tabs.forEach((t) => t.classList.toggle('active', t === tab));
      cards.forEach((card) => {
        const match = cat === 'all' || card.getAttribute('data-category') === cat;
        card.style.display = match ? 'flex' : 'none';
      });
    });
  });
})();
