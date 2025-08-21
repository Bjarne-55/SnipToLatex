"""Toast/notification widget.

This module provides a small, frameless toast used to communicate short, transient
status information near the bottom center of the primary screen. It exposes two
simple states: a loading spinner and a success checkmark.

The implementation is intentionally minimal and self-contained so it can be
reused from anywhere in the application without additional windows.
"""

from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QSize
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QMovie, QPixmap
from pathlib import Path

# Consistent icon size used for spinner and success icon
ICON_SIZE = QSize(30, 30)


class Toast(QWidget):
    """Frameless floating toast widget.

    The toast displays a compact card containing an icon (spinner or checkmark)
    and a single line of text. It shows above all windows and auto-dismisses
    after a short delay in the success state.

    Attributes:
        _card: The inner card widget that holds the content and visual style.
        _icon: Label used to display the spinner or success icon.
        _text: Label used to display the message text.
        _close_timer: Timer used to schedule the auto-dismiss.
        _fade_anim: Opacity animation used for fade-out.
        _loading_movie: Spinner animation movie.
        _check_icon: Pre-scaled success icon pixmap.
    """

    def __init__(self, parent: QWidget = None) -> None:
        """Initialize the toast widget.

        Args:
            parent: Optional parent widget used for window ownership only.
        """
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self._configure_window()
        self._build_ui()
        self._setup_behavior()
        self._load_assets()

    def _configure_window(self) -> None:
        """Configure window flags and attributes for a frameless, floating UI."""
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlag(Qt.NoDropShadowWindowHint, True)

    def _build_ui(self) -> None:
        """Create the card and its internal content layout (icon + text)."""
        self._card = QWidget(self)
        self._card.setObjectName("toastCard")
        self._card.setStyleSheet(
            "#toastCard{background-color: #FFFFFF; border: 1px solid #ababab; border-radius: 10px;}"
        )
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
        content_layout.setContentsMargins(0, 12, 0, 12)
        content_layout.setSpacing(8)

        row = QHBoxLayout()
        row.setContentsMargins(16, 0, 16, 0)
        row.setSpacing(10)
        row.setAlignment(Qt.AlignVCenter)

        self._icon = QLabel(parent)
        self._icon.setAlignment(Qt.AlignCenter)
        self._icon.setFixedSize(ICON_SIZE)

        self._text = QLabel(parent)
        self._text.setStyleSheet("font-family: 'Segoe UI'; color: #000; font-size: 16px; font-weight: 400; background: transparent;")

        row.addWidget(self._icon)
        row.addWidget(self._text)
        row.addItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        content_layout.addLayout(row)
        content_layout.setAlignment(row, Qt.AlignVCenter)

    def _setup_behavior(self) -> None:
        """Initialize timers and animations used by the toast behavior."""
        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self._fade_out_and_hide)

        self.setWindowOpacity(1.0)
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_anim.setDuration(180)

    def _load_assets(self) -> None:
        """Load the spinner movie and success icon pixmap."""
        self._loading_movie = self._load_loading_movie()
        self._check_icon = self._load_check_icon()

    def _place_bottom_center(self) -> None:
        """Place the toast near the bottom-center of the primary screen.

        The widget is horizontally centered with a small horizontal padding to
        avoid screen edges, and vertically positioned slightly above the bottom.
        """
        from PyQt5.QtGui import QGuiApplication

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
        """Show a success state and auto-dismiss after a short delay.

        The spinner is replaced with a checkmark icon and the text is updated.
        The toast remains visible briefly and then fades out automatically.
        """
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
    
    def _load_loading_movie(self) -> QMovie:
        """Create and configure the spinner movie.

        Returns:
            QMovie: The spinner animation sized to ``ICON_SIZE``.
        """
        resource_path = Path(__file__).parent / "resources" / "Rolling@1x-3.3s-200px-200px.gif"
        movie = QMovie(str(resource_path))
        movie.setScaledSize(ICON_SIZE)
        return movie

    def _load_check_icon(self) -> QPixmap:
        """Load and scale the success check icon.

        Returns:
            QPixmap: The success icon pixmap scaled to ``ICON_SIZE``.
        """
        resource_path = Path(__file__).parent / "resources" / "check.svg"
        pixmap = QPixmap(str(resource_path)).scaled(ICON_SIZE, Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)
        return pixmap


