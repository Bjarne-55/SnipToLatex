"""Lightweight toast/notification widget for transient status.

Provides two simple states:
- loading: shows a spinner and message
- success: shows a checkmark and message, then auto-dismisses
"""

from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout


class Toast(QWidget):
    """A frameless floating widget shown above all windows."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlag(Qt.NoDropShadowWindowHint, True)

        # Card container to ensure one single box background
        self._card = QWidget(self)
        self._card.setObjectName("toastCard")

        # Default style (rounded dark background) on the card only
        self._card.setStyleSheet(
            "#toastCard{background-color: rgba(24,24,27,230); border: 1px solid rgba(255,255,255,28); border-radius: 12px;}"
        )

        # Root layout holds the single card
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._card)

        # Inside the card, place icon + text
        self._icon = QLabel(self._card)
        self._text = QLabel(self._card)
        self._text.setStyleSheet("color: white; font-size: 14px; font-weight: 500; background: transparent;")
        self._icon.setStyleSheet("color: #E5E7EB; background: transparent;")

        layout = QHBoxLayout(self._card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        layout.addWidget(self._icon)
        layout.addWidget(self._text)

        # Auto-close timer for success state
        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self._fade_out_and_hide)

        # Track if centered position computed
        self._positioned = False

        # Fade animation using window opacity so we can keep styles simple
        self.setWindowOpacity(1.0)
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_anim.setDuration(180)

        # Keep icon width stable for layout
        self._icon.setFixedWidth(20)

    def _place_bottom_center(self) -> None:
        if self._positioned:
            return
        from PyQt5.QtGui import QGuiApplication

        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        self.adjustSize()
        x = geo.center().x() - self.width() // 2
        y = geo.bottom() - self.height() - 24  # near bottom with margin
        # Keep within screen bounds with small side padding
        left_bound = geo.left() + 12
        right_bound = geo.right() - self.width() - 12
        self.move(max(left_bound, min(x, right_bound)), max(geo.top() + 12, y))
        self._positioned = True

    def show_loading(self, message: str = "Sending to model…") -> None:
        """Show the toast with an indeterminate spinner."""
        # Modern simple loading indicator using unicode to avoid non-transparent GIF artifacts
        self._icon.setMovie(None)
        self._icon.setText("⏳")
        self._icon.setStyleSheet("color: #E5E7EB; background: transparent; font-size: 16px;")

        self._text.setText(message)
        self._close_timer.stop()
        self._positioned = False
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()
        self._place_bottom_center()

    def show_success(self, message: str = "Copied to clipboard") -> None:
        """Show a success state and auto-dismiss after a short delay."""
        self._icon.setMovie(None)
        self._icon.setText("✓")
        self._icon.setStyleSheet("color: #10B981; background: transparent; font-size: 18px;")
        self._text.setText(message)
        self._positioned = False
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self._place_bottom_center()
        # animate a quick fade-in for a subtle success feel
        try:
            self._fade_anim.stop()
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.start()
        except Exception:
            pass
        self._close_timer.start(1500)

    def _fade_out_and_hide(self) -> None:
        try:
            self._fade_anim.stop()
            self._fade_anim.setStartValue(1.0)
            self._fade_anim.setEndValue(0.0)
            # Reconnect finished to hide just for this run
            def _on_finished():
                self.hide()
                self.setWindowOpacity(1.0)  # reset for next show
                try:
                    self._fade_anim.finished.disconnect(_on_finished)
                except Exception:
                    pass
            self._fade_anim.finished.connect(_on_finished)
            self._fade_anim.start()
        except Exception:
            self.hide()


