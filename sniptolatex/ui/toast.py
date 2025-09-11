from __future__ import annotations

"""Toast/notification widget (PyQt6).

This implementation mirrors the web design in ``DesignTemplates/Toast``.
It shows a bottom-centered card with an icon, a title, and a short
description text. Two visual states are supported:

- Loading: animated spinner and waiting copy
- Success: animated checkmark stroke and subtle green glow

The widget is self-contained and can be triggered from anywhere in the app.
"""

# (no file assets needed; icons are painted in code)

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QSize, QPointF, QRectF, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QPen, QPainterPath, QGuiApplication, QRegion
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QFrame,
    QGraphicsDropShadowEffect,
)

from .theme import load_stylesheet

# --------------------------------------------------------------------------------------
# Constants (design tokens and timing)
# --------------------------------------------------------------------------------------

# Icon container size and inner icon sizes (template: 24px box, spinner ~18px)
ICON_BOX = QSize(24, 24)
SPINNER_SIZE = QSize(18, 18)
CHECK_SIZE = QSize(20, 20)

# Spinner motion/appearance
SPINNER_TICK_MS = 16  # ~60 FPS
SPINNER_DEG_PER_TICK = 6
SPINNER_THICKNESS = 3.0
SPINNER_GAP_DEG = 60.0

# Layout
RADIUS_PX = 14
BOTTOM_MARGIN_PX = 24
SIDE_PADDING_PX = 12

# Timing
FADE_OUT_MS = 180
AUTO_DISMISS_MS = 1500

# Colors (keep centralized for easy theme changes)
COLOR_ACCENT_CYAN = QColor(109, 214, 255)    # @accent-cyan
COLOR_ACCENT_VIOLET = QColor(164, 139, 255)  # @accent-violet
COLOR_SUCCESS = QColor(74, 222, 128)         # #4ade80
SUCCESS_GLOW_ALPHA = 0.45
SUCCESS_GLOW_BLUR = 8


def color_with_alpha(color: QColor, alpha: float) -> QColor:
    """Return a copy of ``color`` with the given ``alpha`` multiplier.

    Args:
        color: Base color.
        alpha: Alpha fraction in the range [0, 1].

    Returns:
        QColor: A new color instance with the requested alpha applied.
    """
    c = QColor(color)
    c.setAlpha(int(max(0.0, min(1.0, alpha)) * 255))
    return c


class _Card(QFrame):
    """Rounded card ensuring effects (e.g., glow) respect rounded corners.

    The widget applies a rounded mask on resize so that QGraphicsEffects
    render with the same radius as the visual card.
    """

    def __init__(self, parent: QWidget | None = None, radius: int = RADIUS_PX) -> None:
        super().__init__(parent)
        self._radius = radius
        # Enable styled backgrounds so QSS background is painted
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_mask()

    def _apply_mask(self) -> None:
        r = self.rect()
        if r.isNull():
            return
        path = QPainterPath()
        path.addRoundedRect(QRectF(r), float(self._radius), float(self._radius))
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)


class _Spinner(QWidget):
    """Accent gradient ring spinner.

    A thin ring covering ~300° with a subtle two-tone accent. The start angle
    advances on a timer to create motion.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(SPINNER_SIZE)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(SPINNER_TICK_MS)

        # Colors aligned with theme accents
        self._c1 = COLOR_ACCENT_CYAN
        self._c2 = COLOR_ACCENT_VIOLET

    def _tick(self) -> None:
        self._angle = (self._angle + SPINNER_DEG_PER_TICK) % 360
        self.update()

    def paintEvent(self, _) -> None:  # type: ignore[override]
        thickness = SPINNER_THICKNESS
        gap_deg = SPINNER_GAP_DEG
        start_deg = self._angle * 16
        span_deg = int((360.0 - gap_deg) * 16)

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        pen = QPen()
        pen.setWidthF(thickness)
        # Two-pass draw to emulate an accent gradient
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        rect = QRectF(self.rect()).adjusted(
            thickness / 2.0,
            thickness / 2.0,
            -thickness / 2.0,
            -thickness / 2.0,
        )

        # Base arc in accent cyan
        pen.setColor(self._c1)
        p.setPen(pen)
        p.drawArc(rect, start_deg, span_deg)

        # Overlay shorter arc in accent violet to hint gradient
        pen.setColor(self._c2)
        p.setPen(pen)
        p.drawArc(rect, start_deg + int(span_deg * 0.25), int(span_deg * 0.5))


class _CheckIcon(QWidget):
    """Check icon with stroke-draw animation.

    The check is composed of two straight segments. The animated progress maps
    linearly to the cumulative path length, producing a smooth reveal.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(CHECK_SIZE)
        self._color = COLOR_SUCCESS
        self._progress = 0.0  # 0..1 controls how much of the path is drawn
        self._anim = QPropertyAnimation(self, b"animProgress", self)
        self._anim.setDuration(250)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)

    # Expose animatable property via Qt property so QPropertyAnimation can drive it
    def getAnimProgress(self) -> float:  # noqa: N802
        return self._progress

    def setAnimProgress(self, v: float) -> None:  # noqa: N802
        self._progress = max(0.0, min(1.0, float(v)))
        self.update()
    # Name must match QPropertyAnimation target property
    animProgress = pyqtProperty(float, fget=getAnimProgress, fset=setAnimProgress)

    def start(self) -> None:
        self._anim.stop()
        self._anim.start()

    def _points(self, w: int, h: int) -> tuple[QPointF, QPointF, QPointF]:
        s = float(min(w, h))
        def pt(x: float, y: float) -> QPointF:
            return QPointF(x * s, y * s)
        p0 = pt(0.30, 0.55)
        p1 = pt(0.48, 0.72)
        p2 = pt(0.82, 0.35)
        return p0, p1, p2

    def paintEvent(self, _) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        p0, p1, p2 = self._points(w, h)

        # Compute segment lengths
        def dist(a: QPointF, b: QPointF) -> float:
            dx, dy = (a.x() - b.x()), (a.y() - b.y())
            return (dx*dx + dy*dy) ** 0.5

        L1 = dist(p0, p1)
        L2 = dist(p1, p2)
        total = L1 + L2 if (L1 + L2) > 0 else 1.0
        tlen = max(0.0001, float(self._progress) * total)

        # Build partial path
        partial = QPainterPath(p0)
        if tlen <= L1:
            k = tlen / L1 if L1 > 0 else 0.0
            end = QPointF(p0.x() + (p1.x() - p0.x()) * k, p0.y() + (p1.y() - p0.y()) * k)
            partial.lineTo(end)
        else:
            partial.lineTo(p1)
            rem = min(L2, tlen - L1)
            k = (rem / L2) if L2 > 0 else 1.0
            end = QPointF(p1.x() + (p2.x() - p1.x()) * k, p1.y() + (p2.y() - p1.y()) * k)
            partial.lineTo(end)

        pen = QPen(self._color)
        pen.setWidthF(2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.drawPath(partial)


class Toast(QWidget):
    """Frameless floating toast widget.

    The toast displays a compact card containing an icon (spinner or checkmark)
    and a two-line text. It stays above all windows and auto-dismisses briefly
    after switching to the success state.

    Attributes:
        _card: Inner card that hosts the content and visual style.
        _icon_wrap: Container for icon alignment and sizing.
        _spinner: Loading spinner widget.
        _check: Checkmark widget.
        _title: Title label.
        _desc: Description label.
        _close_timer: Timer for auto-dismiss in success state.
        _fade_anim: Opacity animation for fade out.
        _success_glow: Optional success glow effect for the card.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the toast widget.

        Args:
            parent: Optional parent widget for window ownership.
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self._configure_window()
        self._build_ui()
        self._setup_behavior()
        # Apply QSS for visual style
        try:
            self.setStyleSheet(load_stylesheet("toast"))
        except Exception:
            # In case stylesheet can't be loaded, continue with defaults
            pass

    def _configure_window(self) -> None:
        """Configure window flags and translucent background for a floating UI."""
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)

    def _build_ui(self) -> None:
        """Create the card and its internal content layout (icon + text)."""
        self._card = _Card(self)
        self._card.setObjectName("toastCard")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._card)
        self._build_content(self._card)

    def _build_content(self, parent: QWidget) -> None:
        """Build the icon and text row within the card.

        Args:
            parent: The card widget that hosts the content.
        """
        content_layout = QVBoxLayout(parent)
        content_layout.setContentsMargins(14, 12, 14, 12)
        content_layout.setSpacing(8)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._icon_wrap = QWidget(parent)
        self._icon_wrap.setFixedSize(ICON_BOX)
        icon_layout = QHBoxLayout(self._icon_wrap)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setSpacing(0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._spinner = _Spinner(self._icon_wrap)
        self._check = _CheckIcon(self._icon_wrap)
        self._check.hide()
        icon_layout.addWidget(self._spinner)
        icon_layout.addWidget(self._check)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(4)
        self._title = QLabel(parent)
        self._title.setObjectName("toastTitle")
        self._title.setText("Sending to model…")
        self._desc = QLabel(parent)
        self._desc.setObjectName("toastDesc")
        self._desc.setText("Waiting for a response")
        self._title.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self._desc.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        text_col.addWidget(self._title)
        text_col.addWidget(self._desc)

        row.addWidget(self._icon_wrap)
        row.addLayout(text_col)
        row.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        content_layout.addLayout(row)
        content_layout.setAlignment(row, Qt.AlignmentFlag.AlignVCenter)

    def _setup_behavior(self) -> None:
        """Initialize timers and animations used by the toast behavior."""
        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self._fade_out_and_hide)

        self.setWindowOpacity(1.0)
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_anim.setDuration(FADE_OUT_MS)
        self._success_glow = None  # type: QGraphicsDropShadowEffect | None

    def _place_bottom_center(self) -> None:
        """Place the toast near the bottom-center of the primary screen.

        Horizontally centers the toast and positions it slightly above the
        bottom edge with some side padding to avoid screen edges.
        """
        screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        self.adjustSize()
        x = geo.center().x() - self.width() // 2
        y = geo.bottom() - self.height() - BOTTOM_MARGIN_PX
        # Keep within screen bounds with small side padding
        left_bound = geo.left() + SIDE_PADDING_PX
        right_bound = geo.right() - self.width() - SIDE_PADDING_PX
        self.move(max(left_bound, min(x, right_bound)), max(geo.top() + 12, y))

    def show_loading(self) -> None:
        """Show the loading state with an indeterminate spinner.

        The toast remains visible until another state is shown or it is
        programmatically hidden.
        """
        # Spinner visible, check hidden
        self._spinner.show()
        self._check.hide()
        self._title.setText("Sending to model…")
        self._desc.setText("Waiting for a response")
        # Remove success glow and update border state
        if self._success_glow is not None:
            self._card.setGraphicsEffect(None)
            self._success_glow = None
        self._card.setProperty("state", "loading")
        self._card.style().unpolish(self._card)
        self._card.style().polish(self._card)
        self._close_timer.stop()
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()
        self._place_bottom_center()

    def show_success(self) -> None:
        """Show the success state and auto-dismiss after a short delay.

        Replaces the spinner with an animated checkmark, updates the text, and
        applies a subtle green glow to the card. The toast then fades out.
        """
        self._spinner.hide()
        self._check.show()
        self._check.start()
        self._title.setText("Success")
        self._desc.setText("Response copied to clipboard")
        # Add a subtle green glow around the card
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(SUCCESS_GLOW_BLUR)
        glow.setXOffset(0)
        glow.setYOffset(0)
        glow.setColor(color_with_alpha(COLOR_SUCCESS, SUCCESS_GLOW_ALPHA))
        self._card.setGraphicsEffect(glow)
        self._success_glow = glow
        self._card.setProperty("state", "success")
        self._card.style().unpolish(self._card)
        self._card.style().polish(self._card)
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()
        self._place_bottom_center()
        # animate a quick fade-in for a subtle success feel
        self._close_timer.start(AUTO_DISMISS_MS)


    def _fade_out_and_hide(self) -> None:
        """Fade the toast out and hide it when the animation finishes."""
        self._fade_anim.stop()
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        def _on_finished():
            self.hide()
            self.setWindowOpacity(1.0)
            self._fade_anim.finished.disconnect(_on_finished)
        self._fade_anim.finished.connect(_on_finished)
        self._fade_anim.start()
