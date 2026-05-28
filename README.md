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

For local development, place this folder in Anki's add-on directory and restart Anki:

```text
Anki2/addons21/Pomodoro
```

The add-on entrypoint is `__init__.py`, which loads `pomodoro_qt.controller.setup_addon()`.

To build an installable `.ankiaddon` package, run from the repo root:

```powershell
python package_ankiaddon.py
```

The package is written to `../ankiaddon_dist` by default. The packaging script includes the add-on source/assets and excludes runtime data such as `meta.json`, local state, SQLite databases, logs, caches, and temporary files.

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

Useful validation commands:

```powershell
python -m unittest discover
python -m compileall -q pomodoro_qt
python -m json.tool pomodoro_qt\locales\en.json
python -m json.tool pomodoro_qt\locales\vi.json
git diff --check
```

Focused tests currently cover:

- number formatting by language
- grade-neutral XP behavior
- revlog metric refresh across Anki-day rollover

## Project Layout

```text
pomodoro_qt/              Qt UI, controller, metrics, storage, settings
pomodoro_qt/locales/      English and Vietnamese strings
assets/icons/             UI icons
web/                      legacy/static UI assets
tests/                    unittest test suite
package_ankiaddon.py      safe .ankiaddon packaging script
```

## Packaging Notes

Do not package or commit runtime/user data:

- `meta.json`
- `pomodoro_qt_state.json`
- `pomodoro_qt.db`
- `pomodoro_qt.log`
- cache folders
- temporary files

`package_ankiaddon.py` already excludes these files when building an `.ankiaddon`.
