"""Background image helper for Pomodoro Qt widgets.

Adds a soft, blurred background image behind a QFrame. The image is rendered
with low opacity so foreground widgets stay readable.

The implementation uses a child ``QLabel`` placed below all other children
(via ``lower()`` and ``stackUnder``) and a precomputed blurred pixmap. This
avoids the cost of running a live ``QGraphicsBlurEffect`` on every paint and
plays nicely with QSS styling on the parent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from aqt.qt import (
    QColor,
    QEvent,
    QGraphicsBlurEffect,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QImage,
    QLabel,
    QObject,
    QPainter,
    QPixmap,
    QSize,
    Qt,
    QWidget,
)


def _load_pixmap(path: Path) -> Optional[QPixmap]:
    if not path.is_file():
        return None
    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return None
    return pixmap


def _blur_pixmap(pixmap: QPixmap, radius: float) -> QPixmap:
    """Return a blurred copy of ``pixmap`` using a QGraphicsBlurEffect.

    For radius <= 0 returns the original pixmap unchanged.
    """
    if radius <= 0:
        return pixmap
    item = QGraphicsPixmapItem(pixmap)
    effect = QGraphicsBlurEffect()
    effect.setBlurRadius(radius)
    item.setGraphicsEffect(effect)
    scene = QGraphicsScene()
    scene.addItem(item)
    result = QImage(pixmap.size(), QImage.Format.Format_ARGB32_Premultiplied)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    scene.render(painter, source=scene.itemsBoundingRect())
    painter.end()
    return QPixmap.fromImage(result)


class BgImageLayer(QObject):
    """Wraps a child QLabel that paints the background image inside ``parent``.

    Usage::

        self._bg_layer = BgImageLayer(self)
        self._bg_layer.set_image("/path/to/photo.jpg", opacity=18, blur=8)

    The layer installs an event filter on the parent to resize itself
    automatically; subclasses don't need to override ``resizeEvent``.
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._parent = parent
        self._label = QLabel(parent)
        self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._label.setScaledContents(False)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("background: transparent; border: 0;")
        self._label.lower()
        self._label.hide()

        self._image_path: str = ""
        self._opacity: int = 18
        self._blur: int = 8
        self._dark: bool = False
        self._source: Optional[QPixmap] = None
        self._blurred: Optional[QPixmap] = None
        self._blurred_radius: float = -1.0

        parent.installEventFilter(self)

    # --- public API ----------------------------------------------------------

    def eventFilter(self, obj, event) -> bool:  # noqa: N802 - Qt API
        if obj is self._parent and event.type() == QEvent.Type.Resize:
            self.update_geometry()
        return False

    # --- public API ----------------------------------------------------------

    def set_image(self, path: str, opacity: int, blur: int, *, dark: bool = False) -> None:
        opacity = max(0, min(100, int(opacity)))
        blur = max(0, min(60, int(blur)))
        path_str = str(path or "").strip()

        if not path_str:
            self.clear()
            return

        path_changed = path_str != self._image_path
        self._image_path = path_str
        self._opacity = opacity
        self._blur = blur
        self._dark = bool(dark)

        if path_changed:
            self._source = _load_pixmap(Path(path_str))
            self._blurred = None
            self._blurred_radius = -1.0

        if self._source is None or self._source.isNull():
            self._label.hide()
            return

        self._render()
        self._label.show()
        self._label.lower()

    def clear(self) -> None:
        self._image_path = ""
        self._source = None
        self._blurred = None
        self._blurred_radius = -1.0
        self._label.hide()

    def update_geometry(self) -> None:
        self._label.setGeometry(0, 0, self._parent.width(), self._parent.height())
        if self._source is not None and not self._source.isNull():
            self._render()

    def is_visible(self) -> bool:
        return self._label.isVisible()

    # --- internals -----------------------------------------------------------

    def _render(self) -> None:
        if self._source is None or self._source.isNull():
            return
        size = QSize(max(1, self._parent.width()), max(1, self._parent.height()))
        scaled = self._source.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        # Centre-crop to the widget's exact size.
        cropped = scaled.copy(
            max(0, (scaled.width() - size.width()) // 2),
            max(0, (scaled.height() - size.height()) // 2),
            size.width(),
            size.height(),
        )
        # Apply blur only when radius changes or pixmap base changes.
        if self._blur > 0:
            if self._blurred is None or self._blurred_radius != float(self._blur) or self._blurred.size() != cropped.size():
                self._blurred = _blur_pixmap(cropped, float(self._blur))
                self._blurred_radius = float(self._blur)
            base = self._blurred
        else:
            base = cropped

        # Paint the result with the desired opacity onto a transparent pixmap,
        # then add a soft overlay tinted to the theme so foreground stays readable.
        result = QPixmap(size)
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        painter.setOpacity(max(0.0, min(1.0, self._opacity / 100.0)))
        painter.drawPixmap(0, 0, base)
        # Soft overlay: light theme = white, dark theme = black, ~20% alpha.
        overlay_color = QColor(0, 0, 0, 60) if self._dark else QColor(255, 255, 255, 60)
        painter.setOpacity(1.0)
        painter.fillRect(result.rect(), overlay_color)
        painter.end()

        self._label.setPixmap(result)
        self._label.setGeometry(0, 0, size.width(), size.height())
