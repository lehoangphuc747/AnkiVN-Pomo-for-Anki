"""Shared transparent shell for floating Pomodoro popovers."""

from __future__ import annotations

from typing import Optional

from aqt.qt import (
    QColor,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QPoint,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    Qt,
)

from .style import COLORS


POPUP_FLAGS = Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
HELP_DIVIDER_WIDTH = 1


class _ScrollableHelpPanel(QScrollArea):
    """A fixed-width scroll area that caps its height to a given maximum.

    Content that overflows vertically becomes scrollable instead of stretching
    the parent surface.
    """

    def __init__(self, parent: QWidget, width: int) -> None:
        super().__init__(parent)
        self._panel_width = width
        self.setFixedWidth(width)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(
            """
            QScrollArea { background: transparent; border: 0; }
            QScrollBar:vertical {
                width: 5px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: rgba(0,0,0,0.15);
                border-radius: 2px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            """
        )
        self._inner = QWidget()
        self._inner.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.inner_layout = QVBoxLayout(self._inner)
        self.setWidget(self._inner)

    def cap_height(self, max_height: int) -> None:
        """Set the fixed height so content scrolls instead of growing."""
        h = max(60, max_height)
        self.setFixedHeight(h)


class PopoverShell(QFrame):
    """Transparent top-level popup with a single rounded inner surface.

    Optionally supports a collapsible "help" column on the right that subclasses
    can populate via :meth:`set_help_layout`.
    """

    def __init__(
        self,
        width: int,
        margins: tuple[int, int, int, int] = (16, 16, 16, 16),
        spacing: int = 12,
        shadow_margin: int = 18,
        help_width: int = 260,
        help_margins: Optional[tuple[int, int, int, int]] = None,
        help_spacing: int = 10,
    ) -> None:
        super().__init__(None, POPUP_FLAGS)
        self._main_width = width
        self._help_width = help_width
        self._shadow_margin = shadow_margin
        self._help_visible = False
        self._last_anchor: Optional[QWidget] = None
        self._last_alignment: str = "left"
        self._last_horizontal_offset: int = 0
        self._last_vertical_offset: int = 10

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)

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

        # Inside the surface: main column + (optional) divider + help column.
        outer = QHBoxLayout(self.surface)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._main_panel = QFrame(self.surface)
        self._main_panel.setFixedWidth(width)
        outer.addWidget(self._main_panel, 0, Qt.AlignmentFlag.AlignTop)

        self._help_divider = QFrame(self.surface)
        self._help_divider.setFixedWidth(HELP_DIVIDER_WIDTH)
        self._help_divider.setStyleSheet(f"background: {COLORS['border']}; border: 0;")
        self._help_divider.hide()
        outer.addWidget(self._help_divider)

        self._help_panel = _ScrollableHelpPanel(self.surface, help_width)
        self._help_panel.hide()
        outer.addWidget(self._help_panel, 0, Qt.AlignmentFlag.AlignTop)

        # ``content_layout`` keeps the same name/role as before so existing
        # popover code (add_header / add_progress / etc.) keeps working.
        self.content_layout = QVBoxLayout(self._main_panel)
        self.content_layout.setContentsMargins(*margins)
        self.content_layout.setSpacing(spacing)

        if help_margins is None:
            help_margins = (margins[0], margins[1], margins[2], margins[3])
        self.help_layout = self._help_panel.inner_layout
        self.help_layout.setContentsMargins(*help_margins)
        self.help_layout.setSpacing(help_spacing)

        self._apply_surface_width()

    # --- public API ----------------------------------------------------------

    def clear_content(self) -> None:
        """Reset the main column AND any help content; collapse help panel.

        Subclasses call this at the start of ``refresh_data``. Keeping the help
        collapsed on every refresh matches the agreed UX (no remembered state).
        """
        _clear_layout(self.content_layout)
        _clear_layout(self.help_layout)
        if self._help_visible:
            self._help_visible = False
            self._help_panel.hide()
            self._help_divider.hide()
            self._apply_surface_width()

    def is_help_visible(self) -> bool:
        return self._help_visible

    def toggle_help(self) -> None:
        self.set_help_visible(not self._help_visible)

    def set_help_visible(self, visible: bool) -> None:
        target = bool(visible)
        if target == self._help_visible:
            return
        self._help_visible = target
        self._apply_help_visible()

    def show_at(
        self,
        anchor: QWidget,
        horizontal_alignment: str = "left",
        vertical_offset: int = 10,
        horizontal_offset: int = 0,
    ) -> None:
        self._last_anchor = anchor
        self._last_alignment = horizontal_alignment
        self._last_vertical_offset = vertical_offset
        self._last_horizontal_offset = horizontal_offset
        self._reposition()
        self.show()
        self.raise_()

    # --- internals -----------------------------------------------------------

    def _apply_help_visible(self) -> None:
        self._help_panel.setVisible(self._help_visible)
        self._help_divider.setVisible(self._help_visible)
        if self._help_visible:
            # Cap help panel height to the main panel so it scrolls instead of
            # stretching the whole popover vertically.
            main_height = self._main_panel.sizeHint().height()
            if main_height < 60:
                main_height = self._main_panel.height()
            self._help_panel.cap_height(max(200, main_height))
            # Also lock the help divider to the same height.
            self._help_divider.setFixedHeight(main_height)
        self._apply_surface_width()
        # Force the QHBoxLayout inside ``surface`` to re-run.
        self.surface.updateGeometry()
        layout = self.surface.layout()
        if layout is not None:
            layout.activate()
        if self.isVisible() and self._last_anchor is not None:
            self._reposition()

    def _apply_surface_width(self) -> None:
        total = self._main_width
        if self._help_visible:
            total += HELP_DIVIDER_WIDTH + self._help_width
        self.surface.setFixedWidth(total)
        self.surface.setMinimumWidth(total)
        if self._help_visible:
            # Lock the surface height to the main panel's natural height so the
            # help column scrolls instead of stretching the popover vertically.
            main_height = self._main_panel.sizeHint().height()
            if main_height < 60:
                main_height = self._main_panel.height()
            if main_height > 0:
                self.surface.setFixedHeight(main_height)
        else:
            # Let the surface size naturally when help is collapsed.
            self.surface.setMinimumHeight(0)
            self.surface.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX
        self.setFixedWidth(total + self._shadow_margin * 2)
        self.setMinimumWidth(total + self._shadow_margin * 2)
        self._surface_width = total
        self.adjustSize()

    def _reposition(self) -> None:
        anchor = self._last_anchor
        if anchor is None:
            return
        self.adjustSize()
        left = self._aligned_anchor_left(anchor, self._last_alignment, self._last_horizontal_offset)
        top = anchor.height() + self._last_vertical_offset
        global_pos = anchor.mapToGlobal(QPoint(left, top))
        screen = anchor.screen().availableGeometry()
        surface_width = self.surface.width() or self._surface_width
        surface_height = self.surface.height() or max(1, self.height() - self._shadow_margin * 2)
        surface_left = min(max(screen.left() + 16, global_pos.x()), screen.right() - surface_width - 16)
        surface_top = min(max(screen.top() + 16, global_pos.y()), screen.bottom() - surface_height - 16)
        self.move(surface_left - self._shadow_margin, surface_top - self._shadow_margin)

    def _aligned_anchor_left(self, anchor: QWidget, horizontal_alignment: str, horizontal_offset: int) -> int:
        if horizontal_alignment == "right":
            return anchor.width() - self._main_width + horizontal_offset
        if horizontal_alignment == "center":
            return (anchor.width() - self._main_width) // 2 + horizontal_offset
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
