# AGENTS.md

Quick reference cho AI agents (Codex, Kiro, Cursor, Aider...) làm việc với repo này. Đọc file này trước khi sửa code.

## Project tóm tắt

PomodoroVN là **Anki add-on** chạy trong Anki desktop, dùng PyQt (qua `aqt.qt`). Không phải web app, không phải standalone. Entrypoint: `__init__.py` → `pomodoro_qt.controller.setup_addon()`.

- Python 3.9+ (chạy bên trong Anki nên không có virtualenv)
- UI: PyQt6 (qua wrapper `aqt.qt`)
- Storage: SQLite (`analytics_store.py`) + JSON state
- Ngôn ngữ UI: Tiếng Việt (mặc định) + English

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
pomodoro_qt/
  __init__.py            re-exports
  controller.py          add-on entrypoint, hook đăng ký vào Anki
  ui_manager.py          quản lý 3 layout, dock, popover, dispatch action
  ui_components.py       button factories, icon paths, symbols, COLORS
  widgets.py             compatibility re-exports (legacy)

  under_toolbar.py       layout 1
  sidebar_panel.py       layout 2
  corner_badge.py        layout 3 (Python side)

  models.py              dataclasses, MODE_BREAK/MODE_POMODORO, LAYOUT_*
  timer.py               timer logic
  session_manager.py     session state
  storage.py             persistence wrapper
  analytics_store.py     SQLite store
  config_store.py        Anki config wrapper

  experience_metric.py   tính XP từ revlog
  cards_metric.py        đếm cards studied
  retention_metric.py    tính retention
  streak_metric.py       streak ngày
  study_time_metric.py   tổng thời gian học
  session_history.py     history phiên Pomodoro

  metric_popover.py      popover khi click metric button
  popover_shell.py       shell chung
  html_widgets.py        helper HTML render

  dialogs.py             dialog hoàn thành Pomodoro / break
  settings_dialog.py     dialog Cài đặt
  backup.py              export/import JSON
  backup_manager.py      reset data

  sound.py               audio player + AudioPopover
  audio_volume.py        volume control

  i18n.py                tr(), format_number, current_language
  locales/
    vi.json              tiếng Việt (default)
    en.json              English
  style.py               COLORS palette + Qt stylesheet

assets/icons/            tất cả SVG icon
web/                     pomodoro_ui.html/css/js cho corner badge
tests/                   unittest suite
package_ankiaddon.py     đóng gói .ankiaddon
```

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

### Mở URL ngoài

```python
from aqt.qt import QDesktopServices, QUrl
QDesktopServices.openUrl(QUrl("https://..."))
```

### Đọc revlog Anki

Dùng `pomodoro_qt/anki_day.py` + `revlog_metrics.py`. Không tự query SQLite của Anki trực tiếp. Tôn trọng "Next day starts at" của user (không dùng calendar midnight).

## Quy tắc dữ liệu (quan trọng)

Tách rạch ròi 2 nguồn:

- **Anki-wide Today**: Cards Studied, Retention, Streak, phần XP từ revlog → đọc từ Anki `revlog`, theo ngày Anki.
- **Pomodoro session**: timer state, completed pomos, session history, session XP → lưu trong `analytics_store.py` SQLite.

Không trộn 2 nguồn. Session metric không được "lậm" sang Anki-wide.

## Validation trước khi commit

```powershell
python -m unittest discover
python -m compileall -q pomodoro_qt
python -m json.tool pomodoro_qt\locales\en.json
python -m json.tool pomodoro_qt\locales\vi.json
git diff --check
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

```powershell
python package_ankiaddon.py
```

Output ra `../ankiaddon_dist/PomoVN_<timestamp>.ankiaddon`. Script đã tự exclude runtime data và `__pycache__`.

## Style / convention

- Type hints: dùng (đa số module có)
- f-string thay `.format` trong code, nhưng i18n value dùng `{name}` cho `tr()`
- Kích thước icon button toolbar: `34x34`, icon `20x20`
- Color palette: `pomodoro_qt/style.py::COLORS` — không hardcode hex trong widget
- Dùng `make_toolbar_icon_button`, `make_button`, etc. trong `ui_components.py` thay vì tạo `QPushButton` trần
- Symbol unicode (`SYMBOL_PLAY = "▶"`) chỉ dùng làm fallback khi không có icon SVG

## Tests

```powershell
python -m unittest discover
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
