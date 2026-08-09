# AGENTS.md

Quick reference cho AI agents (Codex, Kiro, Cursor, Aider...) làm việc với repo này. Đọc file này trước khi sửa code.

## Project tóm tắt

PomodoroVN là **Anki add-on** chạy trong Anki desktop, dùng PyQt (qua `aqt.qt`). Không phải web app, không phải standalone. Entrypoint: `src/pomodoro_vn/__init__.py` → `pomodoro_vn.pomodoro_qt.controller.setup_addon()`.

- Python 3.9+ (chạy bên trong Anki nên không có virtualenv)
- UI: PyQt6 (qua wrapper `aqt.qt`)
- Storage: SQLite (`analytics_store.py`) + JSON state
- Ngôn ngữ UI: Tiếng Việt (mặc định) + English
- Build: theo [Anki-Addon-Dev-ToolKit (AADT)](https://github.com/libukai/Anki-Addon-Dev-ToolKit), dùng `uv run aadt build`

## Ngôn ngữ giao tiếp

User nói tiếng Việt. Reply, commit message, và doc reply bằng tiếng Việt khi user dùng tiếng Việt. Code, identifier, tên file giữ nguyên tiếng Anh.

## Layout 3 chế độ hiển thị

Mỗi feature UI thường phải sửa **cả 3 layout**:

| Layout | File | Cách render |
|---|---|---|
| Under Toolbar | `pomodoro_qt/under_toolbar.py` | Qt widget |
| Sidebar Panel | `pomodoro_qt/sidebar_panel.py` | Qt widget |
| Corner Badge | `pomodoro_qt/corner_badge.py` + `web/pomodoro_ui.html` + `web/pomodoro_ui.css` + `web/pomodoro_ui.js` | HTML/JS qua QWebEngineView |

Action từ corner badge HTML đi qua `data-action="..."` → handler trong `ui_manager.py::_handle_corner_action`.

## Module map

```
src/pomodoro_vn/          package chính (module_name theo addon.json)
  __init__.py             Anki entrypoint (lazy load, chỉ chạy khi có aqt)
  config.json             Anki add-on config (commit được, là default/schema config)

src/pomodoro_vn/pomodoro_qt/
  __init__.py            re-exports
  controller.py          add-on entrypoint, hook đăng ký vào Anki
  ui_manager.py          quản lý 3 layout, dock, popover, dispatch action
  ui_components.py       button factories, icon paths, symbols
  widgets.py             compatibility re-exports (legacy)

  anki_bridge.py         đăng ký gui_hooks (answer, profile, sync, day rollover)
  tracking.py            ReviewTracker: theo dõi lượt trả lời thẻ
  anki_day.py            ngày Anki ("Next day starts at"), day_key, cutoff
  revlog_metrics.py      nguồn metric revlog: cards/XP/retention/streak/study time

  under_toolbar.py       layout 1
  sidebar_panel.py       layout 2
  corner_badge.py        layout 3 (Python side)

  models.py              dataclasses, MODE_*, LAYOUT_*, PomodoroSettings
  timer.py               timer logic (bao gồm overtime / Keep going)
  session_manager.py     session state
  storage.py             JSON state wrapper
  analytics_store.py     SQLite store
  config_store.py        Anki config wrapper

  cards_metric.py        đếm cards studied từ revlog
  experience_metric.py   tính XP từ revlog (grade-neutral)
  retention_metric.py    tính retention
  streak_metric.py       streak ngày
  study_time_metric.py   tổng thời gian học

  cards_studied.py       popover factory cho Cards Studied
  experience.py          popover factory cho Experience
  retention.py           popover factory cho Retention
  streaks.py             popover factory cho Streak
  study_time.py          popover factory cho Study Time
  session_history.py     history phiên Pomodoro

  metric_popover.py      popover khi click metric button
  popover_shell.py       shell chung
  html_widgets.py        helper HTML render

  dialogs.py             dialog hoàn thành Pomodoro / break / edit time
  changelog.py           CURRENT_VERSION + so sánh version
  changelog_dialog.py    popup changelog ("Có gì mới")
  settings_dialog.py     dialog Cài đặt
  color_presets.py       7 theme presets + break color
  backup.py              export/import JSON
  backup_manager.py      reset data

  sound.py               audio player + AudioPopover
  audio_volume.py        volume control
  cue_sound.py           start/end cue sounds

  bg_image.py            background image layer
  i18n.py                tr(), format_number, current_language
  locales/
    vi.json              tiếng Việt (default)
    en.json              English
  style.py               COLORS palette + addon_qss() + resolve_colors()

src/pomodoro_vn/assets/icons/    tất cả SVG icon
src/pomodoro_vn/assets/sounds/   audio focus + cue_start.mp3/cue_end.mp3
src/pomodoro_vn/web/             pomodoro_ui.html/css/js cho corner badge
tests/                           unittest suite
addon.json                       metadata AADT (display_name, module_name, build_config)
pyproject.toml                   uv project + dev deps (aadt, pytest, ruff)
```

Lưu ý: `Path(__file__).resolve().parent.parent` trong code trỏ tới `src/pomodoro_vn/` (nơi chứa `assets/`, `web/`, `config.json`, file state runtime).

## Patterns thường gặp

### Thêm 1 toolbar button mới (icon)

1. Copy SVG vào `assets/icons/`
2. Khai báo path trong `ui_components.py`:
   ```python
   FOO_ICON_PATH = ICON_DIR / "foo.svg"
   ```
3. Tạo factory:
   ```python
   def make_foo_button(color=COLORS["muted"], font_size=16) -> QPushButton:
       button = make_toolbar_icon_button("", tr("tooltip.foo"), color, font_size)
       button.setIcon(QIcon(str(FOO_ICON_PATH)))
       button.setIconSize(QSize(20, 20))
       return button
   ```
4. Import + dùng trong `under_toolbar.py` và `sidebar_panel.py`
5. Trong `web/pomodoro_ui.html` thêm `<button data-action="foo" ...>`
6. Trong `corner_badge.py` thêm `foo_icon_src = _svg_data_uri(...)` + key vào `values` dict
7. Trong `ui_manager.py::_handle_corner_action` thêm nhánh `if action == "foo":`
8. Connect signal trong `ui_manager.py::_connect_layout_buttons`
9. Thêm `tooltip.foo` vào **cả** `vi.json` và `en.json`

### Thêm chuỗi i18n

**LUÔN sửa cả 2 file** `locales/vi.json` + `locales/en.json`. Key giống nhau, value khác. Format placeholder: `{name}` (Python `.format`).

### Menu Cài đặt (AnkiVN)

Settings action trong `controller.py::_add_menu_action` cố gắng gắn vào menu AnkiVN có `objectName() == "sf_ankivn_menu"` (tạo bởi Super Free TTS); nếu không thấy thì fallback vào `menuTools`. Đừng hardcode thêm menu khác.

### Config vs state

- `src/pomodoro_vn/config.json` là Anki add-on config → giữ nguyên, commit được. Settings mới (theme, accent, break color, bg tint, bg image, preset, sidebar_side) đều nằm trong `PomodoroSettings` (`models.py`) và được map qua `to_config()` / `from_config()`.
- `suppress_changelog_popup` + `last_changelog_version` nằm trong **data_store JSON** (`storage.py`), không phải config. Khi `controller._record_changelog_seen` cập nhật phải sync cả vào `session_manager._state` để save sau đó không ghi đè mất.

### Mở URL ngoài

```python
from aqt.qt import QDesktopServices, QUrl
QDesktopServices.openUrl(QUrl("https://..."))
```

### Đọc revlog Anki

Dùng `pomodoro_qt/anki_day.py` + `revlog_metrics.py`. Không tự query SQLite của Anki trực tiếp. Tôn trọng "Next day starts at" của user (không dùng calendar midnight).

### Import package trong test

Tests import qua `pomodoro_vn.pomodoro_qt.xxx` (vd: `from pomodoro_vn.pomodoro_qt.i18n import ...`). Chạy test cần `PYTHONPATH=src` hoặc `uv run pytest` (pyproject.toml đã set `pythonpath = ["src"]`). Không import `aqt` ở top-level trong các module test — `src/pomodoro_vn/__init__.py` lazy-load nên import package ngoài Anki không crash.

## Quy tắc dữ liệu (quan trọng)

Tách rạch ròi 2 nguồn:

- **Anki-wide Today**: Cards Studied, Retention, Streak, phần XP từ revlog → đọc từ Anki `revlog`, theo ngày Anki.
- **Pomodoro session**: timer state, completed pomos, session history, session XP → lưu trong `analytics_store.py` SQLite.

Không trộn 2 nguồn. Session metric không được "lậm" sang Anki-wide.

## Validation trước khi commit

```powershell
$env:PYTHONPATH = "src"; python -m unittest discover -s tests
python -m compileall -q src\pomodoro_vn
python -m json.tool src\pomodoro_vn\pomodoro_qt\locales\en.json
python -m json.tool src\pomodoro_vn\pomodoro_qt\locales\vi.json
python -m json.tool addon.json
git diff --check
```

Hoặc dùng uv (aadt đã trong dev group):

```powershell
uv run pytest
```

Khi đụng UI: nhớ test cả 3 layout (under / sidebar / corner). Corner badge dùng HTML/JS nên cần sửa `web/*` riêng.

## Git rules

### KHÔNG bao giờ commit / add / push:

- File có tên bắt đầu bằng `"Nháp để copy gửi cho codex..."` ở root — đây là scratchpad của user
- `meta.json` (Anki tự ghi runtime state vào)
- `pomodoro_qt_state.json`, `pomodoro_qt.db`, `*.log` (runtime data)
- File audio `*.flac`, `*.wav` ở root (đã có bản trong `assets/sounds/`)
- `ankiaddon_dist/`, `__pycache__/`, `.test_tmp/`
- `.vscode/`

### Stage có chọn lọc

`git add .` rất nguy hiểm vì repo thường có WIP của user lẫn lộn. **Stage từng file** mình đã sửa trong session, dùng `git status --short` để verify trước khi commit.

### Commit message

Tiếng Anh (conventional commits OK), nhưng có thể thêm bullet tiếng Việt trong body:

```
feat: short summary

- chi tiết 1
- chi tiết 2
```

Branch hiện tại: `main`. Push thẳng `main` được (đây là personal addon repo).

## Đóng gói .ankiaddon

Dùng AADT build (thay thế `package_ankiaddon.py` đã bỏ):

```powershell
uv run aadt build
```

Output ra `dist/AnkiVN-Pomo-for-Anki-<version>.ankiaddon`. Version lấy từ git tag (không có tag thì đọc từ `pyproject.toml`). Builder tự exclude `.git`, runtime data, `__pycache__`, `dist` theo `archive_exclude_patterns` trong `addon.json`.

Có thể link trực tiếp vào Anki để dev:

```powershell
uv run aadt link        # tạo junction từ src/pomodoro_vn vào addons21
uv run aadt link --unlink
```

## Style / convention

- Type hints: dùng (đa số module có)
- f-string thay `.format` trong code, nhưng i18n value dùng `{name}` cho `tr()`
- Kích thước icon button toolbar: `34x34`, icon `20x20`
- Color palette: `pomodoro_qt/style.py::COLORS` — không hardcode hex trong widget
- Dùng `make_toolbar_icon_button`, `make_button`, etc. trong `ui_components.py` thay vì tạo `QPushButton` trần
- Symbol unicode (`SYMBOL_PLAY = "▶"`) chỉ dùng làm fallback khi không có icon SVG

## Tests

```powershell
$env:PYTHONPATH = "src"; python -m unittest discover -s tests
# hoặc
uv run pytest
```

Coverage hiện tại tập trung:

- format số theo ngôn ngữ (`i18n.py`)
- XP grade-neutral (không phụ thuộc nút Again/Hard/Good/Easy)
- revlog refresh khi Anki day rollover
- audio volume
- study time metric

Khi sửa logic metric, ưu tiên thêm test trong `tests/`.

## Anki API gotchas

- Import Qt qua `aqt.qt`, không import `PyQt6` trực tiếp (Anki có thể dùng PyQt5 hoặc PyQt6 tùy version)
- Hook đăng ký dùng `gui_hooks` trong `aqt`
- `mw` = `aqt.mw` = main window. Nhiều thứ truy cập qua đây
- Đừng block main thread; long task dùng `mw.taskman.run_in_background`
- WebEngine view trong corner badge cần register webview handler qua `mw.web_exporter` / Anki's `aqt.webview` API

## Khi không chắc

- Đọc file đang sửa **trước khi** đổi
- Xem cách feature tương tự đang triển khai (vd: button settings → copy pattern cho button mới)
- Check `tests/` để thấy convention
- Hỏi user thay vì đoán nếu spec mơ hồ
