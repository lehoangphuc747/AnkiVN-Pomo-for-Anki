"""Changelog metadata and popup data for the Pomodoro add-on.

Each entry maps a version string to a per-language ``dict`` of section names
and bullet points.

When the active version differs from the last shown one (and the user has not
suppressed the popup), a dialog summarises every release the user has not yet
seen.
"""

from __future__ import annotations

from typing import Iterable


CURRENT_VERSION = "1.1.11"


# Versions are listed newest first.
CHANGELOG_ENTRIES: list[dict] = [
    {
        "version": "1.1.11",
        "date": "2026-05-17",
        "vi": {
            "Giao diện": [
                "Corner Badge: đổi thứ tự thành Play/Stop/History → Stats → Sound/Feedback/Settings.",
            ],
        },
        "en": {
            "UI": [
                "Corner Badge: reorder to Play/Stop/History → Stats → Sound/Feedback/Settings.",
            ],
        },
    },
    {
        "version": "1.1.10",
        "date": "2026-05-17",
        "vi": {
            "Sửa lỗi": [
                "Sidebar Panel: chữ thời gian trong vòng tròn timer không còn bị chìm trong dark mode.",
                "Vòng nền của timer trong dark mode đổi sang màu tối phù hợp.",
            ],
        },
        "en": {
            "Fixes": [
                "Sidebar Panel: timer text inside the circular ring is now readable in dark mode.",
                "Ring background color also adapts to the active theme.",
            ],
        },
    },
    {
        "version": "1.1.9",
        "date": "2026-05-17",
        "vi": {
            "Giao diện": [
                "Corner Badge: tách hàng controls thành 2 hàng — hàng trên Play / Stop / History, hàng dưới Sound / Feedback / Settings.",
                "Điều chỉnh chiều cao Corner Badge cho khít với nội dung, không còn khoảng trống dưới đáy.",
            ],
        },
        "en": {
            "UI": [
                "Corner Badge: split controls into two rows — top: Play / Stop / History, bottom: Sound / Feedback / Settings.",
                "Tightened Corner Badge height so there is no extra empty space at the bottom.",
            ],
        },
    },
    {
        "version": "1.1.8",
        "date": "2026-05-17",
        "vi": {
            "Sửa lỗi": [
                "Sửa lỗi khi đổi theme trong Preferences của Anki gây RuntimeError do AnkiWebView của PomoVN đã bị xoá nhưng hook theme_did_change vẫn gọi nó.",
                "Cleanup AnkiWebView trước khi destroy widget (Corner Badge và YouTube preview).",
            ],
        },
        "en": {
            "Fixes": [
                "Fix RuntimeError when switching theme in Anki Preferences caused by PomoVN's AnkiWebView being deleted while the theme_did_change hook still referenced it.",
                "Cleanup AnkiWebView properly before destroying widgets (Corner Badge and YouTube preview).",
            ],
        },
    },
    {
        "version": "1.1.7",
        "date": "2026-05-17",
        "vi": {
            "Sửa lỗi": [
                "Corner Badge giữ đúng vị trí khi chuyển giữa Deck → Overview → Study (không còn bị reset).",
            ],
        },
        "en": {
            "Fixes": [
                "Corner Badge keeps its dragged position when navigating between Deck → Overview → Study.",
            ],
        },
    },
    {
        "version": "1.1.6",
        "date": "2026-05-17",
        "vi": {
            "Tính năng mới": [
                "Popup thông báo cập nhật phiên bản. Hiển thị thay đổi theo ngôn ngữ đang chọn.",
                "Tick vào \"Không hiển thị lại\" để tắt popup vĩnh viễn.",
            ],
        },
        "en": {
            "New": [
                "Changelog popup notifies you of new versions in your selected language.",
                "Check \"Don't show this again\" to suppress the popup permanently.",
            ],
        },
    },
    {
        "version": "1.1.5",
        "date": "2026-05-16",
        "vi": {
            "Cải thiện Dark Mode": [
                "Settings dialog cũng follow dark mode (không còn nền sáng).",
                "Chữ \"Pomo\" trong PomoVN đổi thành màu trắng khi dark mode.",
                "Background dark sáng hơn để icon SVG không bị chìm.",
                "Icon control / audio mono trong Corner Badge tự đảo màu khi dark mode.",
            ],
        },
        "en": {
            "Dark Mode polish": [
                "Settings dialog now follows dark mode background.",
                "\"Pomo\" in the PomoVN brand turns white in dark mode.",
                "Dark backgrounds lifted so SVG icons stay visible.",
                "Mono control / audio icons in Corner Badge auto invert in dark mode.",
            ],
        },
    },
    {
        "version": "1.1.4",
        "date": "2026-05-16",
        "vi": {
            "Tính năng mới": [
                "Hỗ trợ Dark Mode: Follow System / Light / Dark.",
                "Tự detect dark mode của hệ điều hành khi chọn Follow System.",
                "Pill switcher chọn theme trong Settings.",
            ],
        },
        "en": {
            "New": [
                "Dark Mode support: Follow System / Light / Dark.",
                "System dark mode auto-detected when Follow System is selected.",
                "Theme pill switcher in Settings.",
            ],
        },
    },
    {
        "version": "1.1.3",
        "date": "2026-05-16",
        "vi": {
            "Tính năng mới": [
                "Sidebar có thể chọn Trái / Phải trong Settings (chỉ hiện khi dùng layout Sidebar).",
            ],
        },
        "en": {
            "New": [
                "Sidebar position can be set to Left or Right in Settings (only visible when Sidebar layout is selected).",
            ],
        },
    },
    {
        "version": "1.1.2",
        "date": "2026-05-16",
        "vi": {
            "Cải thiện": [
                "Có thể kéo cạnh Sidebar để điều chỉnh độ rộng (220–400px).",
            ],
        },
        "en": {
            "Improved": [
                "Sidebar width is now drag-resizable (220–400px).",
            ],
        },
    },
    {
        "version": "1.1.1",
        "date": "2026-05-16",
        "vi": {
            "Cải thiện": [
                "Sidebar: \"Cards Studied\" rút gọn thành \"Studied\".",
                "Sidebar: \"Study Time\" rút gọn thành \"Time\".",
            ],
        },
        "en": {
            "Improved": [
                "Sidebar label \"Cards Studied\" shortened to \"Studied\".",
                "Sidebar label \"Study Time\" shortened to \"Time\".",
            ],
        },
    },
    {
        "version": "1.1.0",
        "date": "2026-05-16",
        "vi": {
            "Tính năng mới": [
                "Toolbar có thêm icon Feedback (mở Google Forms).",
                "Settings: pill switcher dạng tab cho Layout.",
                "Dialog hoàn thành Pomodoro / Break: cho phép nhập số phút trước khi bắt đầu phiên kế tiếp.",
                "Edit Time mới: chỉnh cả Pomodoro và Break time cùng lúc.",
                "Corner Badge: vòng tròn timer là SVG có hiệu ứng sweep.",
                "Corner Badge: bấm vào timer để mở Edit Time.",
                "Corner Badge: metric grid 3+2 (hàng trên 3, hàng dưới 2).",
                "3 built-in sounds: Short Rain, Slow Rain, Rain on Skylight.",
            ],
            "Giao diện": [
                "Experience icon đổi sang ngôi sao vàng.",
                "Sidebar metric order: Experience → Streak → Cards → Study Time → Retention.",
            ],
        },
        "en": {
            "New": [
                "Feedback icon added to the toolbar (opens Google Forms).",
                "Settings: pill switcher for Layout.",
                "Pomodoro / Break done dialogs accept a custom minutes input before starting the next phase.",
                "New Edit Time dialog: adjust Pomodoro and Break minutes together.",
                "Corner Badge: timer ring is now SVG with a sweeping animation.",
                "Corner Badge: click the timer to open Edit Time.",
                "Corner Badge: metric grid is 3+2 (3 on the top row, 2 on the bottom).",
                "Three built-in focus sounds: Short Rain, Slow Rain, Rain on Skylight.",
            ],
            "UI": [
                "Experience icon switched to a yellow star.",
                "Sidebar metric order: Experience → Streak → Cards → Study Time → Retention.",
            ],
        },
    },
]


def _parse_version(version: str) -> tuple:
    parts = []
    for chunk in version.split("."):
        try:
            parts.append(int(chunk))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def entries_since(last_seen: str) -> list[dict]:
    """Return changelog entries newer than the user's last-seen version."""
    if not last_seen:
        return list(CHANGELOG_ENTRIES)
    last_tuple = _parse_version(last_seen)
    return [entry for entry in CHANGELOG_ENTRIES if _parse_version(entry["version"]) > last_tuple]


def has_unseen(last_seen: str) -> bool:
    return bool(entries_since(last_seen))
