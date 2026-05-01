"""UI layout, dock, audio, and metric popover management."""

from __future__ import annotations

from typing import Callable, Optional

from aqt.qt import QDockWidget, QWidget, Qt

from .corner_badge import HtmlCornerBadgeWidget
from .models import LAYOUT_CORNER, LAYOUT_SIDEBAR, LAYOUT_UNDER, SessionMetrics
from .sidebar_panel import SidebarWidget
from .sound import AudioPopover
from .style import addon_qss
from .under_toolbar import UnderToolbarWidget


TOP_DOCK = Qt.DockWidgetArea.TopDockWidgetArea
LEFT_DOCK = Qt.DockWidgetArea.LeftDockWidgetArea
NO_DOCK_FEATURES = QDockWidget.DockWidgetFeature.NoDockWidgetFeatures
UNDER_TOOLBAR_STATES = {"deckBrowser", "overview", "review"}
VISIBLE_LAYOUT_STATES = {"deckBrowser", "overview", "review"}


class UIManager:
    def __init__(
        self,
        mw,
        make_metric_popover: Callable[[str], object],
        refresh_metric_popover: Callable[[str, object], None],
        on_toggle_timer_pause: Callable[[], None],
        on_stop_timer: Callable[[], None],
        on_edit_timer_duration: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_corner_moved: Callable[[int, int], None],
    ) -> None:
        self.mw = mw
        self._make_metric_popover = make_metric_popover
        self._refresh_metric_popover_callback = refresh_metric_popover
        self._on_toggle_timer_pause = on_toggle_timer_pause
        self._on_stop_timer = on_stop_timer
        self._on_edit_timer_duration = on_edit_timer_duration
        self._on_open_settings = on_open_settings
        self._on_corner_moved = on_corner_moved

        self.under_widget: Optional[UnderToolbarWidget] = None
        self.sidebar_widget: Optional[SidebarWidget] = None
        self.corner_widget: Optional[HtmlCornerBadgeWidget] = None
        self.under_dock: Optional[QDockWidget] = None
        self.sidebar_dock: Optional[QDockWidget] = None
        self.audio_popover: Optional[AudioPopover] = None
        self.metric_popovers: dict[str, object] = {}
        self._visible_metric_name: Optional[str] = None
        self._visible_metric_anchor: Optional[QWidget] = None

    def build(self, settings, metrics: SessionMetrics, audio_state: dict) -> None:
        self.under_widget = UnderToolbarWidget(metrics)
        self.sidebar_widget = SidebarWidget(metrics)
        self.corner_widget = HtmlCornerBadgeWidget(metrics)
        self.audio_popover = AudioPopover()
        self.audio_popover.restore_state(audio_state)
        self.metric_popovers = self._make_metric_popovers()

        for widget in [
            self.under_widget,
            self.sidebar_widget,
            self.audio_popover,
            *self.metric_popovers.values(),
        ]:
            widget.setStyleSheet(addon_qss())

        self.under_dock = self._make_dock("PomodoroUnderToolbar", self.under_widget, TOP_DOCK)
        self.sidebar_dock = self._make_dock("PomodoroSidebar", self.sidebar_widget, LEFT_DOCK)
        self.corner_widget.set_saved_position(settings.corner_left, settings.corner_top)

        self._connect_layout_buttons(self.under_widget, floating_audio=True)
        self._connect_layout_buttons(self.sidebar_widget, floating_audio=True)
        self.under_widget.timer_label.clicked.connect(self._on_edit_timer_duration)
        self.corner_widget.action_requested.connect(self._handle_corner_action)
        self.corner_widget.moved.connect(self._on_corner_moved)

    def rebuild(self, settings, metrics: SessionMetrics, audio_state: dict) -> None:
        self.dispose()
        self.build(settings, metrics, audio_state)

    def dispose(self) -> None:
        self.hide_floating_popovers()

        if self.under_dock is not None:
            self.mw.removeDockWidget(self.under_dock)
            self.under_dock.deleteLater()
        if self.sidebar_dock is not None:
            self.mw.removeDockWidget(self.sidebar_dock)
            self.sidebar_dock.deleteLater()
        if self.corner_widget is not None:
            self.corner_widget.hide()
            self.corner_widget.setParent(None)
            self.corner_widget.deleteLater()
        if self.audio_popover is not None:
            self.audio_popover.hide()
            self.audio_popover.deleteLater()
        for popover in self.metric_popovers.values():
            popover.hide()
            popover.deleteLater()

        self.under_widget = None
        self.sidebar_widget = None
        self.corner_widget = None
        self.under_dock = None
        self.sidebar_dock = None
        self.audio_popover = None
        self.metric_popovers = {}
        self._visible_metric_name = None
        self._visible_metric_anchor = None

    def update_visibility(self, settings) -> None:
        self.hide_all_layouts()

        shown_layout = False
        if settings.layout == LAYOUT_UNDER:
            if self._is_under_toolbar_state():
                if self.under_dock:
                    self.under_dock.show()
                shown_layout = True
            self._finish_visibility_update(shown_layout)
            return

        if settings.layout == LAYOUT_SIDEBAR:
            if self._is_visible_layout_state() and self.sidebar_dock:
                self.sidebar_dock.show()
                shown_layout = True
            self._finish_visibility_update(shown_layout)
            return

        if settings.layout == LAYOUT_CORNER:
            if self._is_visible_layout_state():
                self._attach_corner_to_active_area(settings)
            if self._is_visible_layout_state() and self.corner_widget:
                self.corner_widget.show()
                self.corner_widget.raise_()
                shown_layout = True
            self._finish_visibility_update(shown_layout)
            return

        self.hide_floating_popovers()

    def sync_timer_state(self, state) -> None:
        for widget in [self.under_widget, self.sidebar_widget, self.corner_widget]:
            if widget:
                widget.sync_state(state)

    def refresh_metrics(self, metrics: SessionMetrics) -> None:
        for widget in [self.under_widget, self.sidebar_widget, self.corner_widget]:
            if widget:
                widget.refresh_metrics(metrics)
        self.refresh_visible_metric_popover()

    def audio_state_snapshot(self) -> dict:
        if self.audio_popover:
            return self.audio_popover.state_snapshot()
        return {}

    def hide_all_layouts(self) -> None:
        if self.under_dock:
            self.under_dock.hide()
        if self.sidebar_dock:
            self.sidebar_dock.hide()
        if self.corner_widget:
            self.corner_widget.hide()

    def hide_floating_popovers(self) -> None:
        if self.audio_popover:
            self.audio_popover.hide()
        self.hide_metric_popovers()

    def hide_metric_popovers(self) -> None:
        for popover in self.metric_popovers.values():
            popover.hide()
        self._visible_metric_name = None
        self._visible_metric_anchor = None

    def show_metric(self, name: str, anchor: QWidget) -> None:
        popover = self.metric_popovers.get(name)
        if popover is None:
            return
        if popover.isVisible():
            popover.hide()
            self._visible_metric_name = None
            self._visible_metric_anchor = None
            return
        for key, other_popover in self.metric_popovers.items():
            if key != name:
                other_popover.hide()
        self._refresh_metric_popover(name, popover)
        self._visible_metric_name = name
        self._visible_metric_anchor = anchor
        popover.show_at(anchor)

    def refresh_visible_metric_popover(self) -> None:
        name = self._visible_metric_name
        anchor = self._visible_metric_anchor
        if not name or anchor is None or not anchor.isVisible():
            return
        popover = self.metric_popovers.get(name)
        if popover is None or not popover.isVisible():
            return
        self._refresh_metric_popover(name, popover)
        popover.show_at(anchor)

    def _make_dock(self, object_name: str, widget: QWidget, area) -> QDockWidget:
        dock = QDockWidget("", self.mw)
        dock.setObjectName(object_name)
        dock.setWidget(widget)
        dock.setFeatures(NO_DOCK_FEATURES)
        dock.setAllowedAreas(area)
        dock.setTitleBarWidget(QWidget(dock))
        dock.setStyleSheet(addon_qss())
        self.mw.addDockWidget(area, dock)
        dock.hide()
        return dock

    def _connect_layout_buttons(self, widget, floating_audio: bool) -> None:
        widget.pause_button.clicked.connect(self._on_toggle_timer_pause)
        widget.stop_button.clicked.connect(self._on_stop_timer)
        widget.settings_button.clicked.connect(self._on_open_settings)

        if floating_audio:
            widget.audio_button.clicked.connect(lambda _checked=False, button=widget.audio_button: self._toggle_audio(button))

        widget.session_button.clicked.connect(lambda _checked=False, button=widget.session_button: self.show_metric("session", button))
        widget.experience_button.clicked.connect(lambda _checked=False, button=widget.experience_button: self.show_metric("experience", button))
        widget.cards_button.clicked.connect(lambda _checked=False, button=widget.cards_button: self.show_metric("cards", button))
        widget.streak_button.clicked.connect(lambda _checked=False, button=widget.streak_button: self.show_metric("streak", button))
        if hasattr(widget, "retention_button"):
            widget.retention_button.clicked.connect(
                lambda _checked=False, button=widget.retention_button: self.show_metric("retention", button)
            )

    def _make_metric_popovers(self) -> dict:
        popovers = {}
        for name in ["session", "experience", "cards", "retention", "streak"]:
            popover = self._make_metric_popover(name)
            if popover is not None:
                popovers[name] = popover
        return popovers

    def _refresh_metric_popover(self, name: str, popover: object) -> None:
        self._refresh_metric_popover_callback(name, popover)
        popover.setStyleSheet(addon_qss())

    def _toggle_audio(self, anchor: QWidget) -> None:
        if self.audio_popover:
            self.audio_popover.toggle_at(anchor)

    def _handle_corner_action(self, action: str) -> None:
        if action == "pause":
            self._on_toggle_timer_pause()
            return
        if action == "stop":
            self._on_stop_timer()
            return
        if action == "settings":
            self._on_open_settings()
            return
        if action in {"session", "experience", "cards", "streak", "retention"} and self.corner_widget:
            self.show_metric(action, self.corner_widget)

    def _finish_visibility_update(self, shown_layout: bool) -> None:
        if not shown_layout:
            self.hide_floating_popovers()
        else:
            self._hide_popovers_if_anchor_hidden()

    def _hide_popovers_if_anchor_hidden(self) -> None:
        if self.audio_popover and self.audio_popover.isVisible() and not self.audio_popover.anchor_is_visible():
            self.audio_popover.hide()

        anchor = self._visible_metric_anchor
        if anchor is None or anchor.isVisible():
            return
        self.hide_metric_popovers()

    def _is_under_toolbar_state(self) -> bool:
        return getattr(self.mw, "state", None) in UNDER_TOOLBAR_STATES

    def _is_visible_layout_state(self) -> bool:
        return getattr(self.mw, "state", None) in VISIBLE_LAYOUT_STATES

    def _is_review_state(self) -> bool:
        return getattr(self.mw, "state", None) == "review"

    def _attach_corner_to_active_area(self, settings) -> None:
        if not self.corner_widget:
            return
        parent = self._active_area_parent()
        if parent is None:
            return
        if self.corner_widget.parentWidget() is not parent:
            self.corner_widget.setParent(parent)
            self.corner_widget.setStyleSheet(addon_qss())
            self.corner_widget.set_saved_position(settings.corner_left, settings.corner_top)
        self.corner_widget.raise_()

    def _active_area_parent(self) -> Optional[QWidget]:
        if not self._is_review_state():
            return self.mw.centralWidget()
        reviewer = getattr(self.mw, "reviewer", None)
        web = getattr(reviewer, "web", None)
        if web is not None:
            parent = web.parentWidget()
            if parent is not None:
                return parent
            return web
        return self.mw.centralWidget()
