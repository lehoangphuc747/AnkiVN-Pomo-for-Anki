(function () {
  const root = document.getElementById("corner-badge");
  const dragHandle = document.getElementById("drag-handle");
  const modeText = document.getElementById("mode-text");
  const timerText = document.getElementById("timer-text");
  const timerCircle = document.getElementById("timer-circle");
  const timerRingProgress = document.getElementById("timer-ring-progress");
  const pauseButton = document.getElementById("pause-button");
  const stopButton = document.getElementById("stop-button");
  const experienceLevel = document.getElementById("experience-level");
  const cardsCount = document.getElementById("cards-count");
  const studyTimeText = document.getElementById("study-time-text");
  const streakText = document.getElementById("streak-text");
  const retentionText = document.getElementById("retention-text");

  let dragStart = null;
  let pendingDrag = null;
  let dragFrame = 0;
  let suppressHeaderClick = false;

  function send(type, payload) {
    const message = Object.assign({ type }, payload || {});
    if (typeof window.pycmd === "function") {
      window.pycmd("pomodoro:" + JSON.stringify(message));
    }
  }

  function action(name) {
    send("action", { action: name });
  }

  function shadeColor(hex, factor) {
    if (!hex || typeof hex !== "string") return hex;
    let value = hex.trim();
    if (value.startsWith("#")) value = value.slice(1);
    if (value.length === 3) value = value.split("").map((c) => c + c).join("");
    if (value.length !== 6) return hex;
    const num = parseInt(value, 16);
    if (Number.isNaN(num)) return hex;
    let r = (num >> 16) & 0xff;
    let g = (num >> 8) & 0xff;
    let b = num & 0xff;
    if (factor < 0) {
      const amount = Math.min(1, -factor);
      r = Math.round(r * (1 - amount));
      g = Math.round(g * (1 - amount));
      b = Math.round(b * (1 - amount));
    } else {
      const amount = Math.min(1, factor);
      r = Math.round(r + (255 - r) * amount);
      g = Math.round(g + (255 - g) * amount);
      b = Math.round(b + (255 - b) * amount);
    }
    return "#" + [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("");
  }

  function setAccent(color) {
    root.style.setProperty("--anki-red", color);
    const isDark = root.dataset.theme === "dark";
    const dark = shadeColor(color, isDark ? -0.18 : -0.12);
    const light = shadeColor(color, isDark ? -0.55 : 0.86);
    root.style.setProperty("--anki-red-dark", dark);
    root.style.setProperty("--anki-red-light", light);
    timerText.style.color = color;
    if (timerRingProgress) {
      timerRingProgress.setAttribute("stroke", color);
    }
  }

  const RING_CIRCUMFERENCE = 289.027;

  function setProgress(progress) {
    if (!timerRingProgress) return;
    const clamped = Math.max(0, Math.min(1, Number(progress)));
    if (!Number.isFinite(clamped)) {
      return;
    }
    const offset = RING_CIRCUMFERENCE * (1 - clamped);
    timerRingProgress.style.strokeDashoffset = String(offset);
  }

  window.PomodoroUI = {
    update(state) {
      const metrics = state.metrics || {};
      const metricsText = state.metricsText || {};
      const labels = state.labels || {};

      setAccent(state.accent || "#D94B43");
      modeText.textContent = state.label || labels.pomodoro || "Pomodoro";
      timerText.textContent = state.timeText || "25:00";
      setProgress(typeof state.progress === "number" ? state.progress : 1);
      pauseButton.innerHTML = state.paused
        ? `<img src="${pauseButton.dataset.playSrc}" alt="" class="control-icon" />`
        : `<img src="${pauseButton.dataset.pauseSrc}" alt="" class="control-icon" />`;
      stopButton.hidden = !Boolean(state.started);

      experienceLevel.textContent = metricsText.level || String(Math.max(0, safeNumber(metrics.level, 1)));
      cardsCount.textContent = metricsText.cards || String(Math.max(0, safeNumber(metrics.cards, 0)));
      studyTimeText.textContent = metricsText.studyTime || "0m";
      streakText.textContent = metricsText.streakDays || String(Math.max(0, safeNumber(metrics.streakDays, 0)));
      retentionText.textContent =
        metricsText.retention || `${Math.max(0, Math.min(100, safeNumber(metrics.retention, 0)))}%`;
    }
  };

  function safeNumber(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  window.PomodoroBg = {
    apply(dataUri, opacity, blurPx, overlayColor) {
      const layer = document.getElementById("bg-image-layer");
      const overlay = document.getElementById("bg-image-overlay");
      if (!layer || !overlay) return;
      if (dataUri) {
        layer.style.backgroundImage = `url("${dataUri}")`;
        layer.style.opacity = String(Math.max(0, Math.min(1, Number(opacity) || 0)));
        const blur = Math.max(0, Math.min(60, Number(blurPx) || 0));
        layer.style.filter = blur > 0 ? `blur(${blur}px)` : "none";
        overlay.style.background = overlayColor || "transparent";
      } else {
        layer.style.backgroundImage = "";
        layer.style.opacity = "0";
        layer.style.filter = "none";
        overlay.style.background = "transparent";
      }
    }
  };

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
        action("audio");
        return;
      }
      action(name);
    });
  });

  send("ready");
})();
