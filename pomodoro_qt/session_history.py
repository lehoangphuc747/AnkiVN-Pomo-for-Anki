"""iOS-inspired Pomodoro session history popover."""

from __future__ import annotations

from datetime import date, datetime
from typing import Sequence

from aqt.qt import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget, Qt

from .i18n import tr
from .metric_popover import ALIGN_RIGHT, MetricPopover
from .models import MODE_BREAK, MODE_POMODORO, SessionHistoryEntry, SessionMetrics
from .style import COLORS


MAX_TODAY_ROWS = 8
MAX_DAY_ROWS = 45
MAX_SCROLL_HEIGHT = 320

IOS_TEXT = "#1D1D1F"
IOS_SECONDARY = "#6E6E73"
IOS_TERTIARY = "#8E8E93"
IOS_GROUP = "#F5F5F7"
IOS_SEPARATOR = "#E5E5EA"
IOS_RED_SOFT = "#FFF2F0"


class SessionHistoryPopover(MetricPopover):
    def __init__(self, metrics: SessionMetrics, history_snapshot: object = ()) -> None:
        super().__init__(360)
        self.refresh_data(metrics, history_snapshot)

    def refresh_data(self, metrics: SessionMetrics, history_snapshot: object = ()) -> None:
        self.clear_content()
        today_key = _today_key()
        today_entries, day_summaries = _normalize_snapshot(history_snapshot)
        today_summary = _summary_for_day(today_key, day_summaries, today_entries)

        self.content_layout.addWidget(_history_header(metrics, today_summary))
        self.content_layout.addSpacing(12)
        self.content_layout.addWidget(_current_summary_card(metrics))
        self.content_layout.addSpacing(16)
        self.content_layout.addWidget(_section_label(tr("metric.today")))

        if today_entries:
            self.content_layout.addWidget(_today_timeline(today_entries[:MAX_TODAY_ROWS]))
        else:
            self.content_layout.addWidget(_empty_today_card())

        older_days = [summary for summary in day_summaries if summary.get("day") != today_key]
        if older_days:
            self.content_layout.addSpacing(16)
            self.content_layout.addWidget(_section_label(tr("history.previous")))
            self.content_layout.addWidget(_older_days_scroll(older_days[:MAX_DAY_ROWS]))


def make_session_history_popover(
    metrics: SessionMetrics,
    history_snapshot: object = (),
) -> SessionHistoryPopover:
    return SessionHistoryPopover(metrics, history_snapshot)


def _normalize_snapshot(snapshot: object) -> tuple[list[SessionHistoryEntry], list[dict]]:
    if isinstance(snapshot, dict):
        today = [entry for entry in snapshot.get("today", []) if isinstance(entry, SessionHistoryEntry)]
        days = [dict(row) for row in snapshot.get("days", []) if isinstance(row, dict)]
        return sorted(today, key=_sort_key, reverse=True), sorted(days, key=lambda row: str(row.get("day") or ""), reverse=True)

    entries = [entry for entry in snapshot if isinstance(entry, SessionHistoryEntry)] if isinstance(snapshot, Sequence) else []
    today_key = _today_key()
    today = [entry for entry in entries if _date_key(entry.ended_at) == today_key]
    return sorted(today, key=_sort_key, reverse=True), _summaries_from_history(entries)


def _history_header(metrics: SessionMetrics, today_summary: dict) -> QFrame:
    frame = QFrame()
    frame.setObjectName("HistoryHeader")
    frame.setStyleSheet("QFrame#HistoryHeader { background: transparent; border: 0; }")

    layout = QVBoxLayout(frame)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(3)

    eyebrow = QLabel(tr("action.history").upper())
    eyebrow.setStyleSheet(f"font-size: 10px; font-weight: 800; letter-spacing: 1px; color: {COLORS['red']};")

    title = QLabel(_pomodoro_label(metrics.session_index))
    title.setStyleSheet(f"font-size: 19px; font-weight: 650; color: {IOS_TEXT};")

    subtitle = QLabel(_summary_text(today_summary))
    subtitle.setWordWrap(True)
    subtitle.setStyleSheet(f"font-size: 11px; font-weight: 500; color: {IOS_SECONDARY};")

    layout.addWidget(eyebrow)
    layout.addWidget(title)
    layout.addWidget(subtitle)
    return frame


def _current_summary_card(metrics: SessionMetrics) -> QFrame:
    card = QFrame()
    card.setObjectName("HistoryCurrentCard")
    card.setStyleSheet(
        f"""
        QFrame#HistoryCurrentCard {{
            background: {IOS_RED_SOFT};
            border: 1px solid #F6D9D5;
            border-radius: 16px;
        }}
        """
    )
    layout = QVBoxLayout(card)
    layout.setContentsMargins(12, 11, 12, 12)
    layout.setSpacing(10)

    title_row = QHBoxLayout()
    title_row.setContentsMargins(0, 0, 0, 0)
    title_row.setSpacing(8)

    title = QLabel(tr("state.current"))
    title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {IOS_TEXT};")
    badge = QLabel(_pomodoro_label(metrics.session_index))
    badge.setAlignment(ALIGN_RIGHT)
    badge.setStyleSheet(
        f"""
        background: white;
        border: 1px solid #F2CCC7;
        border-radius: 10px;
        color: {COLORS['red']};
        font-size: 10px;
        font-weight: 750;
        padding: 3px 8px;
        """
    )
    title_row.addWidget(title)
    title_row.addStretch(1)
    title_row.addWidget(badge)
    layout.addLayout(title_row)

    stats = QHBoxLayout()
    stats.setContentsMargins(0, 0, 0, 0)
    stats.setSpacing(8)
    stats.addWidget(_stat_pill(tr("common.cards"), str(max(0, metrics.session_cards)), IOS_TEXT), 1)
    stats.addWidget(_stat_pill(tr("metric.retention"), f"{max(0, metrics.session_retention)}%", COLORS["green"]), 1)
    stats.addWidget(_stat_pill(tr("common.xp"), f"+{max(0, metrics.session_xp)}", COLORS["red"]), 1)
    layout.addLayout(stats)
    return card


def _stat_pill(label_text: str, value_text: str, color: str) -> QFrame:
    pill = QFrame()
    pill.setObjectName("HistoryStatPill")
    pill.setStyleSheet(
        f"""
        QFrame#HistoryStatPill {{
            background: white;
            border: 1px solid {IOS_SEPARATOR};
            border-radius: 12px;
        }}
        """
    )
    layout = QVBoxLayout(pill)
    layout.setContentsMargins(9, 7, 9, 7)
    layout.setSpacing(1)

    value = QLabel(value_text)
    value.setAlignment(Qt.AlignmentFlag.AlignCenter)
    value.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {color};")
    label = QLabel(label_text.upper())
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet(f"font-size: 9px; font-weight: 700; color: {IOS_TERTIARY}; letter-spacing: 0.5px;")

    layout.addWidget(value)
    layout.addWidget(label)
    return pill


def _today_timeline(entries: list[SessionHistoryEntry]) -> QFrame:
    group = QFrame()
    group.setObjectName("HistoryTimelineGroup")
    group.setStyleSheet(
        f"""
        QFrame#HistoryTimelineGroup {{
            background: {IOS_GROUP};
            border: 1px solid {IOS_SEPARATOR};
            border-radius: 16px;
        }}
        """
    )
    layout = QVBoxLayout(group)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(0)

    for index, entry in enumerate(entries):
        layout.addWidget(_timeline_row(entry, is_last=index == len(entries) - 1))
    return group


def _timeline_row(entry: SessionHistoryEntry, is_last: bool) -> QFrame:
    row = QFrame()
    row.setObjectName("HistoryTimelineRow")
    row.setStyleSheet("QFrame#HistoryTimelineRow { background: transparent; border: 0; }")

    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)

    marker_box = QFrame()
    marker_box.setObjectName("HistoryMarkerBox")
    marker_box.setFixedWidth(28)
    marker_box.setStyleSheet("QFrame#HistoryMarkerBox { background: transparent; border: 0; }")
    marker_layout = QVBoxLayout(marker_box)
    marker_layout.setContentsMargins(0, 0, 0, 0)
    marker_layout.setSpacing(4)

    accent = _entry_accent(entry)
    marker = QLabel(_entry_marker(entry))
    marker.setFixedSize(26, 26)
    marker.setAlignment(Qt.AlignmentFlag.AlignCenter)
    marker.setStyleSheet(
        f"""
        background: {accent};
        border: 0;
        border-radius: 13px;
        color: white;
        font-size: 11px;
        font-weight: 800;
        """
    )
    marker_layout.addWidget(marker, 0, Qt.AlignmentFlag.AlignHCenter)

    if not is_last:
        connector = QFrame()
        connector.setFixedWidth(1)
        connector.setMinimumHeight(30)
        connector.setStyleSheet(f"background: {IOS_SEPARATOR}; border: 0;")
        marker_layout.addWidget(connector, 1, Qt.AlignmentFlag.AlignHCenter)

    text_box = QFrame()
    text_box.setObjectName("HistoryTimelineText")
    text_box.setStyleSheet("QFrame#HistoryTimelineText { background: transparent; border: 0; }")
    text_layout = QVBoxLayout(text_box)
    text_layout.setContentsMargins(0, 1, 0, 12 if not is_last else 0)
    text_layout.setSpacing(3)

    title_row = QHBoxLayout()
    title_row.setContentsMargins(0, 0, 0, 0)
    title_row.setSpacing(8)

    title = QLabel(_entry_title(entry))
    title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {IOS_TEXT};")
    time = QLabel(_time_text(entry.ended_at))
    time.setAlignment(ALIGN_RIGHT)
    time.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {accent};")
    title_row.addWidget(title)
    title_row.addStretch(1)
    title_row.addWidget(time)

    detail = QLabel(_entry_detail(entry))
    detail.setWordWrap(True)
    detail.setStyleSheet(f"font-size: 11px; font-weight: 500; color: {IOS_SECONDARY};")

    text_layout.addLayout(title_row)
    text_layout.addWidget(detail)

    layout.addWidget(marker_box)
    layout.addWidget(text_box, 1)
    return row


def _empty_today_card() -> QFrame:
    card = QFrame()
    card.setObjectName("HistoryEmptyToday")
    card.setStyleSheet(
        f"""
        QFrame#HistoryEmptyToday {{
            background: {IOS_GROUP};
            border: 1px solid {IOS_SEPARATOR};
            border-radius: 16px;
        }}
        """
    )
    layout = QVBoxLayout(card)
    layout.setContentsMargins(12, 11, 12, 11)
    layout.setSpacing(4)

    title = QLabel(_summary_text({"pomodoros": 0, "cards": 0, "xp": 0}))
    title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {IOS_TEXT};")
    detail = QLabel(tr("session.subtitle_today"))
    detail.setWordWrap(True)
    detail.setStyleSheet(f"font-size: 11px; font-weight: 500; color: {IOS_SECONDARY};")

    layout.addWidget(title)
    layout.addWidget(detail)
    return card


def _older_days_scroll(summaries: list[dict]) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setMaximumHeight(MAX_SCROLL_HEIGHT)
    scroll.setStyleSheet(
        f"""
        QScrollArea {{
            background: transparent;
            border: 0;
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 5px;
            margin: 4px 0;
        }}
        QScrollBar::handle:vertical {{
            background: #D1D1D6;
            border-radius: 2px;
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0;
            border: 0;
        }}
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        """
    )

    content = QWidget()
    content.setStyleSheet("background: transparent;")
    layout = QVBoxLayout(content)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(_day_group(summaries))
    scroll.setWidget(content)
    return scroll


def _day_group(summaries: list[dict]) -> QFrame:
    group = QFrame()
    group.setObjectName("HistoryDayGroup")
    group.setStyleSheet(
        f"""
        QFrame#HistoryDayGroup {{
            background: {IOS_GROUP};
            border: 1px solid {IOS_SEPARATOR};
            border-radius: 16px;
        }}
        """
    )
    layout = QVBoxLayout(group)
    layout.setContentsMargins(0, 2, 0, 2)
    layout.setSpacing(0)

    for index, summary in enumerate(summaries):
        layout.addWidget(_day_summary_row(summary))
        if index < len(summaries) - 1:
            layout.addWidget(_separator())
    return group


def _day_summary_row(summary: dict) -> QFrame:
    row = QFrame()
    row.setObjectName("HistoryDayRow")
    row.setStyleSheet("QFrame#HistoryDayRow { background: transparent; border: 0; }")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(12, 9, 12, 9)
    layout.setSpacing(10)

    label = QLabel(_day_label(str(summary.get("day") or "")))
    label.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {IOS_TEXT};")
    detail = QLabel(_summary_text(summary))
    detail.setAlignment(ALIGN_RIGHT)
    detail.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {IOS_SECONDARY};")

    layout.addWidget(label)
    layout.addStretch(1)
    layout.addWidget(detail)
    return row


def _separator() -> QFrame:
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet(f"background: {IOS_SEPARATOR}; border: 0; margin-left: 12px;")
    return line


def _section_label(text: str) -> QLabel:
    label = QLabel(text.upper())
    label.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {IOS_TERTIARY}; letter-spacing: 1px; padding: 0 2px 6px 2px;")
    return label


def _entry_title(entry: SessionHistoryEntry) -> str:
    if entry.mode == MODE_BREAK:
        return tr("session.break")
    return _pomodoro_label(entry.session_index)


def _entry_detail(entry: SessionHistoryEntry) -> str:
    status = tr("state.completed") if entry.completed else tr("state.stopped")
    if entry.mode == MODE_BREAK:
        return tr("session.history_break_detail", status=status, minutes=_minutes(entry.duration_seconds))
    deck = tr("session.deck_suffix", deck=entry.deck_name.strip()) if entry.deck_name.strip() else ""
    return tr(
        "session.history_focus_detail",
        status=status,
        minutes=_minutes(entry.duration_seconds),
        cards=max(0, entry.cards),
        retention=max(0, entry.retention),
        xp=max(0, entry.xp),
        deck=deck,
    )


def _entry_marker(entry: SessionHistoryEntry) -> str:
    if entry.mode == MODE_BREAK:
        return "B"
    return str(_positive_index(entry.session_index))


def _entry_accent(entry: SessionHistoryEntry) -> str:
    return COLORS["green"] if entry.mode == MODE_BREAK else COLORS["red"]


def _pomodoro_label(index: object) -> str:
    return f"Pomodoro {_positive_index(index)}"


def _positive_index(value: object) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = 1
    return max(1, parsed)


def _summary_for_day(day: str, summaries: list[dict], entries: list[SessionHistoryEntry]) -> dict:
    for summary in summaries:
        if summary.get("day") == day:
            return summary
    fallback = _summaries_from_history(entries)
    return fallback[0] if fallback else {"day": day, "pomodoros": 0, "breaks": 0, "cards": 0, "xp": 0}


def _summary_text(summary: dict) -> str:
    pomodoros = _int(summary.get("pomodoros"))
    cards = _int(summary.get("cards"))
    xp = _int(summary.get("xp"))
    return f"{pomodoros} Pomo - {cards} {tr('common.cards')} - {xp} {tr('common.xp')}"


def _summaries_from_history(history: Sequence[SessionHistoryEntry]) -> list[dict]:
    summaries: dict[str, dict] = {}
    for entry in history:
        day = _date_key(entry.ended_at)
        if not day:
            continue
        summary = summaries.setdefault(day, {"day": day, "pomodoros": 0, "breaks": 0, "cards": 0, "xp": 0})
        if entry.mode == MODE_POMODORO:
            summary["pomodoros"] += 1
        elif entry.mode == MODE_BREAK:
            summary["breaks"] += 1
        summary["cards"] += max(0, entry.cards)
        summary["xp"] += max(0, entry.xp)
    return [summaries[key] for key in sorted(summaries.keys(), reverse=True)]


def _today_key() -> str:
    return date.today().isoformat()


def _date_key(value: str) -> str:
    parsed = _parse_datetime(value)
    return parsed.date().isoformat() if parsed is not None else ""


def _day_label(day_key: str) -> str:
    try:
        parsed = date.fromisoformat(day_key)
    except ValueError:
        return day_key or "--"
    return parsed.strftime("%d/%m")


def _time_text(value: str) -> str:
    parsed = _parse_datetime(value)
    return parsed.strftime("%H:%M") if parsed is not None else "--:--"


def _minutes(seconds: int) -> int:
    return max(0, round(seconds / 60))


def _sort_key(entry: SessionHistoryEntry) -> str:
    return entry.ended_at or entry.started_at or ""


def _parse_datetime(value: str):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone()
    return parsed


def _int(value: object) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


__all__ = ["SessionHistoryPopover", "make_session_history_popover"]
