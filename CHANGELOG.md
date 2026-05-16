# Changelog

Lịch sử thay đổi PomodoroVN. Bắt đầu từ version 1.1.0.

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
