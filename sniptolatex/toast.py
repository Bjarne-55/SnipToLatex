"""Lightweight toast/notification widget for transient status.

Provides two simple states:
- loading: shows a spinner and message
- success: shows a checkmark and message, then auto-dismisses
"""

from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QSize
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QToolButton, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QMovie, QPixmap
from pathlib import Path


class Toast(QWidget):
    """A frameless floating widget shown above all windows."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlag(Qt.NoDropShadowWindowHint, True)

        # Card container to ensure one single box background
        self._card = QWidget(self)
        self._card.setObjectName("toastCard")

        # White card style similar to system toast
        self._card.setStyleSheet(
            "#toastCard{background-color: #FFFFFF; border: 1px solid #ababab; border-radius: 10px;}"
        )

        # Root layout holds the single card
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._card)

        # Inside the card, create top content row and bottom accent bar
        content_layout = QVBoxLayout(self._card)
        content_layout.setContentsMargins(0, 12, 0, 12)
        content_layout.setSpacing(8)

        row = QHBoxLayout()
        row.setContentsMargins(16, 0, 16, 0)
        row.setSpacing(10)
        row.setAlignment(Qt.AlignVCenter)

        self._icon = QLabel(self._card)
        self._icon.setAlignment(Qt.AlignCenter)
        self._icon.setFixedSize(30, 30)

        self._text = QLabel(self._card)
        self._text.setStyleSheet("font-family: 'Segoe UI'; color: #000; font-size: 16px; font-weight: 400; background: transparent;")

        row.addWidget(self._icon)
        row.addWidget(self._text)
        row.addItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        content_layout.addLayout(row)
        content_layout.setAlignment(row, Qt.AlignVCenter)

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

        # load spinning animation and check icon
        self._loading_movie = self._load_loading_movie()
        self._check_icon = self._load_check_icon()

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

    def show_loading(self) -> None:
        """Show the toast with an indeterminate spinner."""
        # Spinner inside a neutral circle
        self._icon.setPixmap(QPixmap())
        self._icon.setMovie(self._loading_movie)
        self._loading_movie.start()
        self._icon.setText("")
        
        self._text.setText("Sending to model")
        self._close_timer.stop()
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()
        self._place_bottom_center()

    def show_success(self) -> None:
        """Show a success state and auto-dismiss after a short delay."""
        self._loading_movie.stop()
        self._icon.setMovie(None)
        self._icon.setText("")
        self._icon.setPixmap(self._check_icon)

        self._text.setText("Copied to clipboard")
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()
        self._place_bottom_center()
        # animate a quick fade-in for a subtle success feel
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
    
    def _load_loading_movie(self) -> QMovie:
        resource_path = Path(__file__).parent / "resources" / "Rolling@1x-3.3s-200px-200px.gif"
        movie = QMovie(str(resource_path))
        movie.setScaledSize(self._icon.size())
        return movie

    def _load_check_icon(self) -> QPixmap:
        resource_path = Path(__file__).parent / "resources" / "check.svg"
        pixmap = QPixmap(str(resource_path))
        pixmap = pixmap.scaled(self._icon.size(), Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)
        return pixmap


