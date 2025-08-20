"""Interactive full-desktop selection overlay.

This topmost frameless widget covers the virtual desktop and lets the user
drag to select a rectangle. It dispatches the selection to the capture layer
and then closes itself.
"""

from PyQt5.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QGuiApplication, QMouseEvent, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QWidget, QPushButton

from .capture import capture_and_copy, get_virtual_geometry
from .settings_dialog import SettingsDialog


class SelectionOverlay(QWidget):
    """Translucent overlay for selecting a screen region.

    Attributes:
        closed (pyqtSignal): Emitted when the overlay closes.
        _dragging (bool): Whether the user is currently dragging a selection.
        _start (QPoint): Global coordinates where the drag started.
        _end (QPoint): Global coordinates of the current/last mouse position.
        _virtual_rect (QRect): The virtual desktop rectangle covering all monitors.
        _overlay_color (QColor): Semi-transparent fill color for dimming background.
        _border_pen (QPen): Pen used to draw the selection border.
        settings_button (QPushButton): Button to open the settings dialog.
    """
    closed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__(None)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.CrossCursor)
        self.setFocusPolicy(Qt.StrongFocus)

        self._dragging = False
        self._start = QPoint()
        self._end = QPoint()
        self._virtual_rect = get_virtual_geometry()
        self.setGeometry(self._virtual_rect)

        self._overlay_color = QColor(0, 0, 0, 100)
        self._border_pen = QPen(QColor(0, 153, 255, 220), 2, Qt.SolidLine)

        self.settings_button = QPushButton("⚙", self)
        self.settings_button.setFixedSize(32, 32)
        self.settings_button.move(12, 12)
        self.settings_button.setStyleSheet(
            "QPushButton{background: rgba(20,20,20,180); color: white; border: 1px solid rgba(255,255,255,120); border-radius: 4px;}"
            "QPushButton:hover{background: rgba(40,40,40,200);}" 
        )
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.clicked.connect(self._open_settings)

    def _open_settings(self) -> None:
        """Open the settings dialog."""
        released = False
        try:
            self.releaseKeyboard()
            released = True
        except Exception:
            pass
        dlg = SettingsDialog(self)
        dlg.exec_()
        if released:
            try:
                self.grabKeyboard()
            except Exception:
                pass

    def begin(self) -> None:
        """Show the overlay across all monitors and prepare for dragging."""
        self._virtual_rect = get_virtual_geometry()
        self.setGeometry(self._virtual_rect)
        self._dragging = False
        self._start = QPoint()
        self._end = QPoint()
        self.show()
        self.raise_()
        self.activateWindow()
        try:
            self.grabKeyboard()
        except Exception:
            pass
        self.setFocus(Qt.MouseFocusReason)

    def keyPressEvent(self, event):
        """Allow Escape to cancel the overlay.

        Args:
            event (QKeyEvent): The key event.
        """
        if event.key() == Qt.Key_Escape:
            self.close()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start selection on left click; right click cancels.

        Args:
            event (QMouseEvent): The mouse press event.
        """
        if event.button() == Qt.RightButton:
            self.close()
            return
        if event.button() == Qt.LeftButton:
            if self.settings_button.geometry().contains(event.pos()):
                self.settings_button.click()
                return
            self._dragging = True
            self._start = event.globalPos()
            self._end = self._start
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Update the selection rectangle while dragging.

        Args:
            event (QMouseEvent): The mouse move event.
        """
        if not self._dragging:
            return
        self._end = event.globalPos()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Finalize selection and trigger capture.

        Args:
            event (QMouseEvent): The mouse release event.
        """
        if event.button() != Qt.LeftButton:
            return
        if not self._dragging:
            return
        self._dragging = False
        self._end = event.globalPos()
        rect = QRect(self._start, self._end).normalized()
        capture_rect = QRect(
            rect.left() - self._virtual_rect.left(),
            rect.top() - self._virtual_rect.top(),
            rect.width(),
            rect.height(),
        )
        capture_and_copy(capture_rect)
        self.close()

    def paintEvent(self, _event) -> None:
        """Render dark overlay with a clear selection rectangle and border.

        Args:
            _event (QPaintEvent): The paint event (unused).
        """
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.HighQualityAntialiasing)
        painter.fillRect(self.rect(), self._overlay_color)
        if not self._start.isNull() and not self._end.isNull():
            rect = QRect(self.mapFromGlobal(self._start), self.mapFromGlobal(self._end)).normalized()
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setPen(self._border_pen)
            painter.drawRect(rect)

    def closeEvent(self, event):
        """Emit close signal and release keyboard properly.

        Args:
            event (QCloseEvent): The close event.
        """
        try:
            self.closed.emit()
        finally:
            try:
                self.releaseKeyboard()
            except Exception:
                pass
            super().closeEvent(event)


