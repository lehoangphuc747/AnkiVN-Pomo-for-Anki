# PomodoroVN

PomodoroVN is a Qt-based Anki add-on for running Pomodoro study sessions inside Anki. It adds compact timer controls, study metrics, session history, focus audio, and backup/reset tools without moving Anki-wide review counts into Pomodoro session state.

## Features

- Pomodoro and break timer with configurable durations.
- Three display modes: Under Toolbar, Sidebar Panel, and Corner Badge.
- Study metrics for Experience, Cards Studied, Retention, Streak, and Session History.
- Cards Studied, Retention, and Streak read from Anki `revlog` using Anki's Today window.
- Pomodoro session history stays separate from Anki-wide Today metrics.
- Focus audio controls with built-in sounds and YouTube link support.
- Settings backup/import plus separate reset actions for study data and all data.
- Vietnamese and English UI strings.

## Install

For local development, link the add-on source into Anki using AADT (recommended), or copy the package folder:

```text
Anki2/addons21/pomodoro_vn
```

The add-on entrypoint is `src/pomodoro_vn/__init__.py`, which loads `pomodoro_vn.pomodoro_qt.controller.setup_addon()`.

To build an installable `.ankiaddon` package, run from the repo root:

```powershell
uv run aadt build
```

The package is written to `dist/AnkiVN-Pomo-for-Anki-<version>.ankiaddon`. AADT includes the add-on source/assets and excludes runtime data such as `meta.json`, local state, SQLite databases, logs, caches, and temporary files (see `archive_exclude_patterns` in `addon.json`).

## Usage

Open Anki after installing the add-on. PomodoroVN appears according to the configured layout:

- `Under Toolbar`: compact controls under Anki's toolbar.
- `Sidebar Panel`: a left dock panel with timer and metrics.
- `Corner Badge`: a floating badge inside the active Anki area.

Use the Settings button to change:

- layout
- Pomodoro and break duration
- auto-start behavior
- language
- backup/import/reset options

The timer can be started, paused, resumed, stopped, and edited from the UI.

## Metrics

PomodoroVN intentionally separates two kinds of data:

- Anki-wide Today metrics: Cards Studied, Retention, Streak, and the revlog-based part of Experience.
- Pomodoro-session metrics: current session progress, completed Pomodoros, session history, and Pomodoro bonus XP.

Cards Studied and Retention count Anki review answer events in Anki's Today window. This means they follow Anki's "Next day starts at" setting instead of the calendar midnight boundary. When the Anki day rolls over, Today values refresh for the new day.

Session History is local to PomodoroVN and tracks Pomodoro sessions, breaks, session cards, session retention, session XP, and deck context.

## Data And Backups

PomodoroVN stores different kinds of data separately:

- Anki add-on config: user settings.
- Runtime state: timer/audio/session state.
- Analytics SQLite data: Pomodoro session and review-event history used by local history views.
- Anki `revlog`: Anki-owned source of truth for Today-wide review metrics.

Use Settings -> Export data to create a JSON backup. Use Import data to replace current PomodoroVN settings and study data from a backup file.

Reset options:

- Reset study data: clears study/session/timer data while keeping settings.
- Reset all: clears study data and restores settings to defaults.

## Development

This project uses [AADT](https://github.com/libukai/Anki-Addon-Dev-ToolKit) with a `src/` layout, `uv` for dependency management, and AADT for building/linking.

```powershell
uv sync --group dev       # install dev dependencies (aadt, pytest, ruff)
uv run aadt link          # link src/pomodoro_vn into Anki addons21 (dev)
uv run aadt build         # build .ankiaddon into dist/
```

Useful validation commands:

```powershell
$env:PYTHONPATH = "src"; python -m unittest discover -s tests
python -m compileall -q src\pomodoro_vn
python -m json.tool src\pomodoro_vn\pomodoro_qt\locales\en.json
python -m json.tool src\pomodoro_vn\pomodoro_qt\locales\vi.json
git diff --check
```

Focused tests currently cover:

- number formatting by language
- grade-neutral XP behavior
- revlog metric refresh across Anki-day rollover

## Project Layout

```text
src/pomodoro_vn/          add-on package (module_name = pomodoro_vn)
src/pomodoro_vn/pomodoro_qt/   Qt UI, controller, metrics, storage, settings
src/pomodoro_vn/pomodoro_qt/locales/  English and Vietnamese strings
src/pomodoro_vn/assets/    icons and focus/cue sounds
src/pomodoro_vn/web/       corner badge HTML/JS/CSS
src/pomodoro_vn/config.json     Anki add-on config schema/defaults
tests/                    unittest test suite
addon.json                AADT build metadata
pyproject.toml            uv project + dev dependencies
```

## Packaging Notes

Do not package or commit runtime/user data:

- `meta.json`
- `pomodoro_qt_state.json`
- `pomodoro_qt.db`
- `pomodoro_qt.log`
- cache folders
- temporary files

`aadt build` already excludes these files (see `archive_exclude_patterns` in `addon.json`).
