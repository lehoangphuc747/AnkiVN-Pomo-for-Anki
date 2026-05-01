"""Shared transparent shell for floating Pomodoro popovers."""

from __future__ import annotations

from aqt.qt import QColor, QFrame, QGraphicsDropShadowEffect, QPoint, QVBoxLayout, QWidget, Qt

from .style import COLORS


POPUP_FLAGS = Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint


class PopoverShell(QFrame):
    """Transparent top-level popup with a single rounded inner surface."""

    def __init__(
        self,
        width: int,
        margins: tuple[int, int, int, int] = (16, 16, 16, 16),
        spacing: int = 12,
        shadow_margin: int = 18,
    ) -> None:
        super().__init__(None, POPUP_FLAGS)
        self._surface_width = width
        self._shadow_margin = shadow_margin
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)
        self.setFixedWidth(width + shadow_margin * 2)

        try:
            self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        except AttributeError:
            pass

        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(shadow_margin, shadow_margin, shadow_margin, shadow_margin)
        wrapper.setSpacing(0)

        self.surface = QFrame(self)
        self.surface.setObjectName("PomodoroPopoverSurface")
        self.surface.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.surface.setFixedWidth(width)
        self.surface.setStyleSheet(
            f"""
            QFrame#PomodoroPopoverSurface {{
                background: #FFFFFF;
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
            }}
            """
        )
        if shadow_margin > 0:
            shadow = QGraphicsDropShadowEffect(self.surface)
            shadow.setBlurRadius(28)
            shadow.setOffset(0, 8)
            shadow.setColor(QColor(62, 60, 56, 46))
            self.surface.setGraphicsEffect(shadow)
        wrapper.addWidget(self.surface)

        self.content_layout = QVBoxLayout(self.surface)
        self.content_layout.setContentsMargins(*margins)
        self.content_layout.setSpacing(spacing)

    def clear_content(self) -> None:
        _clear_layout(self.content_layout)

    def show_at(
        self,
        anchor: QWidget,
        horizontal_alignment: str = "left",
        vertical_offset: int = 10,
        horizontal_offset: int = 0,
    ) -> None:
        self.adjustSize()
        left = self._aligned_anchor_left(anchor, horizontal_alignment, horizontal_offset)
        top = anchor.height() + vertical_offset
        global_pos = anchor.mapToGlobal(QPoint(left, top))
        screen = anchor.screen().availableGeometry()
        surface_width = self.surface.width() or self._surface_width
        surface_height = self.surface.height() or max(1, self.height() - self._shadow_margin * 2)
        surface_left = min(max(screen.left() + 16, global_pos.x()), screen.right() - surface_width - 16)
        surface_top = min(max(screen.top() + 16, global_pos.y()), screen.bottom() - surface_height - 16)
        self.move(surface_left - self._shadow_margin, surface_top - self._shadow_margin)
        self.show()
        self.raise_()

    def _aligned_anchor_left(self, anchor: QWidget, horizontal_alignment: str, horizontal_offset: int) -> int:
        if horizontal_alignment == "right":
            return anchor.width() - self._surface_width + horizontal_offset
        if horizontal_alignment == "center":
            return (anchor.width() - self._surface_width) // 2 + horizontal_offset
        return horizontal_offset


def _clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.hide()
            widget.setParent(None)
            widget.deleteLater()
            continue
        child_layout = item.layout()
        if child_layout is not None:
            _clear_layout(child_layout)
            child_layout.setParent(None)
