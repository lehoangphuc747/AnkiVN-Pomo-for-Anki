(function () {
  const root = document.getElementById("corner-badge");
  const dragHandle = document.getElementById("drag-handle");
  const modeText = document.getElementById("mode-text");
  const timerText = document.getElementById("timer-text");
  const pauseButton = document.getElementById("pause-button");
  const stopButton = document.getElementById("stop-button");
  const experienceLevel = document.getElementById("experience-level");
  const cardsCount = document.getElementById("cards-count");
  const streakText = document.getElementById("streak-text");
  const retentionText = document.getElementById("retention-text");
  const audioPlayButton = document.getElementById("audio-play-button");

  let dragStart = null;
  let pendingDrag = null;
  let dragFrame = 0;
  let suppressHeaderClick = false;
  let audioOpen = false;
  let audioPlaying = false;

  function send(type, payload) {
    const message = Object.assign({ type }, payload || {});
    if (typeof window.pycmd === "function") {
      window.pycmd("pomodoro:" + JSON.stringify(message));
    }
  }

  function action(name) {
    send("action", { action: name });
  }

  function setAccent(color) {
    root.style.setProperty("--anki-red", color);
    timerText.style.color = color;
  }

  window.PomodoroUI = {
    update(state) {
      const metrics = state.metrics || {};
      const metricsText = state.metricsText || {};
      const labels = state.labels || {};

      setAccent(state.accent || "#D94B43");
      modeText.textContent = state.label || labels.pomodoro || "Pomodoro";
      timerText.textContent = state.timeText || "25:00";
      pauseButton.innerHTML = state.paused
        ? `<img src="${pauseButton.dataset.playSrc}" alt="" class="control-icon" />`
        : `<img src="${pauseButton.dataset.pauseSrc}" alt="" class="control-icon" />`;
      stopButton.hidden = !Boolean(state.started);

      experienceLevel.textContent = metricsText.level || String(Math.max(0, safeNumber(metrics.level, 1)));
      cardsCount.textContent = metricsText.cards || String(Math.max(0, safeNumber(metrics.cards, 0)));
      streakText.textContent = metricsText.streakDays || String(Math.max(0, safeNumber(metrics.streakDays, 0)));
      retentionText.textContent =
        metricsText.retention || `${Math.max(0, Math.min(100, safeNumber(metrics.retention, 0)))}%`;
    }
  };

  function safeNumber(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function flushDrag() {
    dragFrame = 0;
    if (!pendingDrag) return;
    send("dragMove", pendingDrag);
    pendingDrag = null;
  }

  function queueDrag(dx, dy) {
    pendingDrag = { dx, dy };
    if (dragFrame) return;
    dragFrame = window.requestAnimationFrame(flushDrag);
  }

  dragHandle.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    suppressHeaderClick = false;
    dragStart = {
      x: event.screenX,
      y: event.screenY,
      moved: false
    };
    dragHandle.setPointerCapture(event.pointerId);
    send("dragStart");
  });

  dragHandle.addEventListener("pointermove", (event) => {
    if (!dragStart) return;
    event.preventDefault();
    const dx = Math.round(event.screenX - dragStart.x);
    const dy = Math.round(event.screenY - dragStart.y);
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) {
      dragStart.moved = true;
      suppressHeaderClick = true;
    }
    queueDrag(dx, dy);
  });

  function finishDrag(event) {
    if (!dragStart) return;
    const moved = dragStart.moved;
    if (pendingDrag) {
      flushDrag();
    }
    if (dragFrame) {
      window.cancelAnimationFrame(dragFrame);
      dragFrame = 0;
    }
    dragStart = null;
    try {
      dragHandle.releasePointerCapture(event.pointerId);
    } catch (_error) {
      // Pointer capture can already be released by WebEngine.
    }
    send("dragEnd");
    if (moved) {
      suppressHeaderClick = true;
      window.setTimeout(() => {
        suppressHeaderClick = false;
      }, 0);
    }
  }

  dragHandle.addEventListener("pointerup", finishDrag);
  dragHandle.addEventListener("pointercancel", finishDrag);
  dragHandle.addEventListener("click", (event) => {
    if (!suppressHeaderClick) return;
    event.preventDefault();
    event.stopPropagation();
    suppressHeaderClick = false;
  });

  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", (event) => {
      const name = event.currentTarget.dataset.action;
      if (name === "audio") {
        audioOpen = !audioOpen;
        root.classList.toggle("audio-open", audioOpen);
        send("audioToggled", { expanded: audioOpen });
        return;
      }
      action(name);
    });
  });

  if (audioPlayButton) {
    audioPlayButton.addEventListener("click", () => {
      audioPlaying = !audioPlaying;
      const icon = audioPlaying ? audioPlayButton.dataset.pauseSrc : audioPlayButton.dataset.playSrc;
      audioPlayButton.innerHTML = `<img src="${icon}" alt="" class="audio-control-icon play-icon" />`;
      audioPlayButton.setAttribute("aria-pressed", String(audioPlaying));
    });
  }

  send("ready");
})();
