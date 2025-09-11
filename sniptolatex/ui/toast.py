from __future__ import annotations

"""Toast/notification widget (PyQt6).

Matches the design template in DesignTemplates/Toast:
 - Bottom-centered card with icon + title + description
 - Two states: loading (spinner) and success (check + green glow)

This widget is self-contained and can be triggered from anywhere.
"""

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QSize, QPointF, QRectF, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QPen, QPainterPath, QGuiApplication
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

# Icon container size and inner icon sizes (template: 24px box, spinner ~18px)
ICON_BOX = QSize(24, 24)
SPINNER_SIZE = QSize(18, 18)
CHECK_SIZE = QSize(20, 20)


class _Spinner(QWidget):
    """Accent gradient ring spinner sized to SPINNER_SIZE.

    Draws a 300° arc with a gradient and rotates it using a timer.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(SPINNER_SIZE)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60fps

        # Colors aligned with theme accents
        self._c1 = QColor(0x6D, 0xD6, 0xFF)  # @accent-cyan
        self._c2 = QColor(0xA4, 0x8B, 0xFF)  # @accent-violet

    def _tick(self) -> None:
        self._angle = (self._angle + 6) % 360  # rotate ~360deg/sec
        self.update()

    def paintEvent(self, _) -> None:  # type: ignore[override]
        thickness = 3.0
        gap_deg = 60.0  # gap for spinner arc
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
    """Check icon with stroke-draw animation."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(CHECK_SIZE)
        self._color = QColor(0x4A, 0xDE, 0x80)  # #4ade80
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
    and a single line of text. It shows above all windows and auto-dismisses
    after a short delay in the success state.

    Attributes:
        _card: The inner card widget that holds the content and visual style.
        _icon_wrap: Container for icon sizing/alignment.
        _spinner: Loading spinner widget.
        _check: Success checkmark widget.
        _title: Title label.
        _desc: Description label.
        _close_timer: Timer used to schedule the auto-dismiss.
        _fade_anim: Opacity animation used for fade-out.
    """

    def __init__(self, parent: QWidget = None) -> None:
        """Initialize the toast widget.

        Args:
            parent: Optional parent widget used for window ownership only.
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
        """Configure window flags and attributes for a frameless, floating UI."""
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)

    def _build_ui(self) -> None:
        """Create the card and its internal content layout (icon + text)."""
        self._card = QFrame(self)
        self._card.setObjectName("toastCard")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._card)
        self._build_content(self._card)

    def _build_content(self, parent: QWidget) -> None:
        """Build the icon and text row within the card.

        Args:
            parent: The card widget that will host the content.
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
        self._fade_anim.setDuration(180)
        self._success_glow = None  # type: QGraphicsDropShadowEffect | None

    def _place_bottom_center(self) -> None:
        """Place the toast near the bottom-center of the primary screen.

        The widget is horizontally centered with a small horizontal padding to
        avoid screen edges, and vertically positioned slightly above the bottom.
        """
        screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        self.adjustSize()
        x = geo.center().x() - self.width() // 2
        y = geo.bottom() - self.height() - 24  # near bottom with margin
        # Keep within screen bounds with small side padding
        left_bound = geo.left() + 12
        right_bound = geo.right() - self.width() - 12
        self.move(max(left_bound, min(x, right_bound)), max(geo.top() + 12, y))

    def show_loading(self) -> None:
        """Show a loading state with an indeterminate spinner.

        The toast is displayed immediately and remains visible until another
        state is shown (e.g., ``show_success``) or the application hides it.
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
        """Show a success state and auto-dismiss after a short delay.

        The spinner is replaced with a checkmark icon and the text is updated.
        The toast remains visible briefly and then fades out automatically.
        """
        self._spinner.hide()
        self._check.show()
        self._check.start()
        self._title.setText("Success")
        self._desc.setText("Reponse copied to clipboard")
        # Add a subtle green glow around the card
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(8)
        glow.setXOffset(0)
        glow.setYOffset(0)
        glow.setColor(QColor(74, 222, 128, int(0.45 * 255)))
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
        self._close_timer.start(1500)


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
