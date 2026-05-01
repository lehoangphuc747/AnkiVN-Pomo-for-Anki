(function () {
  const root = document.getElementById("corner-badge");
  const dragHandle = document.getElementById("drag-handle");
  const modeText = document.getElementById("mode-text");
  const timerText = document.getElementById("timer-text");
  const ringProgress = document.getElementById("ring-progress");
  const pauseButton = document.getElementById("pause-button");
  const stopButton = document.getElementById("stop-button");
  const sessionText = document.getElementById("session-text");
  const experienceButton = document.getElementById("experience-button");
  const experienceLevel = document.getElementById("experience-level");
  const experienceXp = document.getElementById("experience-xp");
  const cardsButton = document.getElementById("cards-button");
  const cardsCount = document.getElementById("cards-count");
  const xpProgress = document.getElementById("xp-progress");
  const streakButton = document.getElementById("streak-button");
  const streakText = document.getElementById("streak-text");
  const streakCaption = document.getElementById("streak-caption");
  const audioButton = document.getElementById("audio-button");
  const audioPlayButton = document.getElementById("audio-play-button");

  let dragStart = null;
  let audioOpen = false;
  let audioPlaying = false;
  const circumference = 2 * Math.PI * 16;

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
    ringProgress.style.stroke = color;
    xpProgress.style.background = color;
  }

  window.PomodoroUI = {
    update(state) {
      const metrics = state.metrics || {};
      const labels = state.labels || {};
      const progress = Math.max(0, Math.min(1, Number(state.progress || 0)));
      const offset = circumference - progress * circumference;

      setAccent(state.accent || "#D94B43");
      modeText.textContent = state.label || labels.pomodoro || "Pomodoro";
      timerText.textContent = state.timeText || "25:00";
      ringProgress.style.strokeDasharray = String(circumference);
      ringProgress.style.strokeDashoffset = String(offset);
      pauseButton.innerHTML = state.paused
        ? `<img src="${pauseButton.dataset.playSrc}" alt="" class="control-icon" />`
        : `<img src="${pauseButton.dataset.pauseSrc}" alt="" class="control-icon" />`;
      stopButton.hidden = !Boolean(state.started);

      sessionText.textContent = `${labels.pomodoro || "Pomodoro"} ${safeNumber(metrics.sessionIndex, 1)}`;
      experienceLevel.textContent = `${labels.levelShort || "Lv"} ${safeNumber(metrics.level, 1)}`;
      experienceXp.textContent = `${safeNumber(metrics.totalXp, 0)} / ${safeNumber(metrics.nextLevelXp, 20)} XP`;
      cardsCount.textContent = `+${safeNumber(metrics.cards, 0)}`;
      streakText.textContent = state.streakText || `${safeNumber(metrics.streakDays, 0)}d`;
      streakCaption.textContent = state.streakCaption || labels.streakCaption || "";
      xpProgress.style.width = `${Math.max(0, Math.min(100, safeNumber(metrics.levelProgress, 0)))}%`;
    }
  };

  function safeNumber(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  dragHandle.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    dragStart = { x: event.clientX, y: event.clientY };
    dragHandle.setPointerCapture(event.pointerId);
    send("dragStart");
  });

  dragHandle.addEventListener("pointermove", (event) => {
    if (!dragStart) return;
    event.preventDefault();
    send("dragMove", {
      dx: Math.round(event.clientX - dragStart.x),
      dy: Math.round(event.clientY - dragStart.y)
    });
  });

  function finishDrag(event) {
    if (!dragStart) return;
    dragStart = null;
    try {
      dragHandle.releasePointerCapture(event.pointerId);
    } catch (_error) {
      // Pointer capture can already be released by WebEngine.
    }
    send("dragEnd");
  }

  dragHandle.addEventListener("pointerup", finishDrag);
  dragHandle.addEventListener("pointercancel", finishDrag);

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
