# Changelog

Lịch sử thay đổi PomodoroVN. Bắt đầu từ version 1.1.0.

---

## [1.1.5] - 2026-05-16

### Cải thiện Dark Mode

- **Settings dialog follow dark mode** — thêm rule `QDialog` background/text vào QSS để dialog không còn nền sáng khi dark mode.
- **"Pomo" trắng trong dark mode** — chữ "Pomo" của brand "PomoVN" hiển thị màu trắng (`#FFFFFF`), giữ "VN" màu đỏ nhấn mạnh. Áp dụng cho Sidebar, Under Toolbar, Corner Badge.
- **Background sáng hơn cho icon SVG** — palette dark điều chỉnh: `bg #2A2A2C`, `window #34343A`, `border #4A4A4F` (thay vì `#1E1E1E`/`#252525` quá tối). SVG icon dark navy không còn bị "chìm".
- **Icon filter cho corner badge** — control icons & audio icons mono dark nhận `filter: brightness(0) invert(1)` chỉ trong dark mode, đảm bảo visible. Icons có màu (star, fire...) không filter.
- Helper `active_colors()` / `is_dark_active()` cho phép code Python query active palette.

---

## [1.1.4] - 2026-05-16

### Tính năng mới

- **Dark Mode** — hỗ trợ 3 chế độ: Follow System, Light, Dark. Tự detect OS dark mode qua QApplication palette. Pill switcher trong Settings.
- Dark palette (`COLORS_DARK`) với nền tối, accent colors điều chỉnh cho contrast.
- `addon_qss()` nhận theme parameter, tất cả widget và dialog áp dụng theme từ settings.

---

## [1.1.3] - 2026-05-16

### Tính năng mới

- **Sidebar Left/Right** — khi chọn layout Sidebar trong Settings, hiện thêm pill switcher chọn vị trí Trái/Phải.
- Dock widget đặt vào `LEFT_DOCK` hoặc `RIGHT_DOCK` theo setting.
- Field `sidebar_side` mới trong PomodoroSettings.

---

## [1.1.2] - 2026-05-16

### Cải thiện

- **Sidebar resizable** — người dùng có thể kéo cạnh sidebar để điều chỉnh độ rộng (220–400px).

---

## [1.1.1] - 2026-05-16

### Cải thiện

- **Sidebar labels ngắn gọn** — "Cards Studied" → "Studied", "Study Time" → "Time" trong Sidebar Panel.

---

## [1.1.0] - 2026-05-16

### Tính năng mới

- **Feedback button** — thêm icon "?" trên toolbar (trước icon Settings) ở cả 3 layout. Click mở Google Forms góp ý & báo lỗi.
- **Animated pill switcher** — thay combobox layout trong Settings bằng tab switcher dạng viên thuốc có hiệu ứng trượt mượt.
- **Done dialog cho phép chọn thời gian** — sau khi hoàn thành Pomodoro, user có thể nhập số phút break trước khi bắt đầu. Tương tự sau break, user nhập số phút Pomodoro tiếp theo.
- **Edit Time dialog mới** — click vào thời gian cho phép chỉnh cả Pomodoro time và Break time cùng lúc (thay vì chỉ 1 loại).
- **Corner badge SVG ring** — thay border tĩnh bằng vòng tròn SVG có hiệu ứng sweep counterclockwise (giống sidebar CircularProgress).
- **Corner badge timer clickable** — bấm vào vòng tròn thời gian trong Corner Badge mở Edit Time dialog.
- **Corner badge metric grid 3+2** — hàng trên 3 chip (Experience, Streak, Cards), hàng dưới 2 chip (Study Time, Retention).
- **3 built-in sounds** — đăng ký đủ 3 file âm thanh: Short Rain Loop, Slow Rain Loop, Rain on Skylight.

### Thay đổi giao diện

- **Experience icon** — đổi sang ngôi sao vàng (`star-svgrepo-com.svg`), fill `#FBC02D`.
- **Experience text/color** — chữ level và icon đều màu vàng ở cả 3 layout.
- **Sidebar metric order** — Experience → Streak → Cards Studied → Study Time → Retention.
- **EN label** — "Status style" → "Style"; "PomodoroVN time" → "Pomodoro time".

### Sửa lỗi & cải thiện

- Fix profile switch không rebind addon state.
- Refresh revlog metrics khi Anki day rollover.
- XP tính từ unique cards (grade-neutral, không phụ thuộc nút Again/Hard/Good/Easy).
- Cards Studied align với Anki stats (dùng Anki Today window).
- Thay file `.flac` bằng `.wav` cho slow rain loop (tương thích tốt hơn).
- Dọn file audio trùng lặp ở root.

### Docs

- Thêm `AGENTS.md` — quick reference cho AI agents làm việc với repo.
- Thêm `CHANGELOG.md` — file này.

---

## [1.0.0] - 2026-05-03

### Initial release

- Pomodoro timer với 3 layout: Under Toolbar, Sidebar Panel, Corner Badge.
- Study metrics: Experience (XP/Level), Cards Studied, Retention, Streak, Session History.
- Focus audio với built-in sounds và YouTube link.
- Settings dialog: layout, thời gian, auto-start, ngôn ngữ.
- Backup/Import/Reset dữ liệu.
- Hỗ trợ Tiếng Việt và English.
- Đóng gói `.ankiaddon` qua `package_ankiaddon.py`.
