(function () {
  const root = document.getElementById("corner-badge");
  const dragHandle = document.getElementById("drag-handle");
  const modeEmoji = document.getElementById("mode-emoji");
  const modeText = document.getElementById("mode-text");
  const timerText = document.getElementById("timer-text");
  const ringProgress = document.getElementById("ring-progress");
  const pauseButton = document.getElementById("pause-button");
  const stopButton = document.getElementById("stop-button");
  const sessionText = document.getElementById("session-text");
  const experienceButton = document.getElementById("experience-button");
  const cardsButton = document.getElementById("cards-button");
  const xpProgress = document.getElementById("xp-progress");
  const streakButton = document.getElementById("streak-button");
  const audioButton = document.getElementById("audio-button");

  let dragStart = null;
  let audioOpen = false;
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
      modeEmoji.textContent = state.mode === "break" ? "\u2615" : "\ud83c\udf45";
      modeText.textContent = state.label || labels.pomodoro || "Pomodoro";
      timerText.textContent = state.timeText || "25:00";
      ringProgress.style.strokeDasharray = String(circumference);
      ringProgress.style.strokeDashoffset = String(offset);
      pauseButton.textContent = state.paused ? "\u25b6" : "\u23f8";
      stopButton.hidden = !Boolean(state.started);

      sessionText.textContent = `${metrics.sessionIndex || 1} / ${metrics.sessionTotal || 4}`;
      experienceButton.innerHTML = `<strong>${labels.levelShort || "Lv"} ${metrics.level || 1}</strong> ${metrics.totalXp || 0}/${metrics.nextLevelXp || 20}`;
      cardsButton.innerHTML = `\u26a1 <span>+${metrics.cards || 0}</span>`;
      streakButton.innerHTML = `\ud83d\udd25 <span>${state.streakText || `${metrics.streakDays || 0}d`}</span>`;
      xpProgress.style.width = `${Math.max(0, Math.min(100, metrics.levelProgress || 0))}%`;
    }
  };

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

  send("ready");
})();
