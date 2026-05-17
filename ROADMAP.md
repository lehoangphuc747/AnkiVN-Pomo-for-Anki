# PomodoroVN Roadmap

Danh sách các feature đang plan, bug cần xử lý, và ý tưởng cho các phiên bản tiếp theo. Khác với `CHANGELOG.md` (ghi những gì đã ship), file này ghi những gì **chưa làm**.

> Cập nhật khi có ý tưởng mới hoặc khi item được hoàn thành (move sang CHANGELOG).

---

## 🐛 Bug & Compatibility

### High priority

- [ ] **Sidebar Panel Left xung đột với SynapsePro**
  - Add-on liên quan: [🧠 SynapsePro - The Ultimate Anki Add-On](https://ankiweb.net/shared/info/236979321)
  - Hiện tượng: SynapsePro cũng dock một panel ở vị trí Left → chen lấn / che mất Sidebar Panel của PomoVN khi cả hai cùng bật.
  - Hướng fix gợi ý:
    - Detect SynapsePro qua `mw.addonManager` và auto fallback sang `sidebar_side = right` nếu user chưa pick.
    - Hoặc cho user một option "share dock area" để xếp dock theo `splitDockWidget` thay vì stack lên nhau.
    - Tối thiểu: hiện warning trong Settings khi cả hai add-on đều chọn Left.

---

## 🚀 Feature ideas (chưa có timeline)

- [ ] Custom XP per card / per minute
- [ ] Pomodoro presets (25/5, 50/10, 90/20, ...) chọn nhanh từ Corner Badge
- [ ] Auto-pause timer khi máy idle quá X phút
- [ ] Export changelog summary ra hình ảnh để share lên social
- [ ] Dark mode tự follow Anki theme thay vì OS

---

## 🎨 UI polish

- [ ] Icon vẽ lại theo style nhất quán (tomato + star + brain hiện đang khác bộ)
- [ ] Animation cho metric chip khi giá trị thay đổi (pulse / count-up)
- [ ] Hiệu ứng confetti nhẹ khi hoàn thành Pomodoro

---

## 🧪 Test & DX

- [ ] Coverage cho `session_manager.record_answer`
- [ ] Coverage cho `corner_badge` JS bridge (mock pycmd)
- [ ] CI script chạy `python -m unittest discover` + `compileall` mỗi commit

---

## 📝 Docs

- [ ] Screenshot mới cho Sidebar Panel (Left/Right + resizable)
- [ ] Screenshot Dark Mode để dùng trong AnkiWeb description
- [ ] Hướng dẫn export/import backup chi tiết hơn
