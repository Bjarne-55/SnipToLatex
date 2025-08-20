#!/usr/bin/env python3
import sys
import signal
import threading
from typing import Optional

from pynput import keyboard

from PyQt5.QtCore import QPoint, QRect, Qt, QSize, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QColor, QGuiApplication, QMouseEvent, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QDialog, QVBoxLayout, QLabel


def get_virtual_geometry() -> QRect:
    screens = QGuiApplication.screens()
    if not screens:
        return QRect(0, 0, 0, 0)
    geom = screens[0].geometry()
    for s in screens[1:]:
        geom = geom.united(s.geometry())
    return geom


def grab_full_desktop_pixmap() -> Optional[QPixmap]:
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return None
    pix = screen.grabWindow(0)
    if not pix or pix.isNull():
        screens = QGuiApplication.screens()
        if not screens:
            return None
        virtual_rect = get_virtual_geometry()
        if virtual_rect.width() <= 0 or virtual_rect.height() <= 0:
            return None
        stitched = QPixmap(virtual_rect.size())
        stitched.fill(Qt.transparent)
        painter = QPainter(stitched)
        try:
            for s in screens:
                s_pix = s.grabWindow(0)
                if s_pix and not s_pix.isNull():
                    offset = s.geometry().topLeft() - virtual_rect.topLeft()
                    painter.drawPixmap(offset, s_pix)
        finally:
            painter.end()
        return stitched
    return pix


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Placeholder settings", self))
        layout.addWidget(QLabel("- Option A: ...", self))
        layout.addWidget(QLabel("- Option B: ...", self))
        self.resize(320, 200)


class SelectionOverlay(QWidget):
    closed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__(None)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.CrossCursor)
        self.setFocusPolicy(Qt.StrongFocus)

        self._dragging: bool = False
        self._start: QPoint = QPoint()
        self._end: QPoint = QPoint()
        self._virtual_rect: QRect = get_virtual_geometry()
        self.setGeometry(self._virtual_rect)

        self._overlay_color = QColor(0, 0, 0, 100)
        self._border_pen = QPen(QColor(0, 153, 255, 220), 2, Qt.SolidLine)

        # Settings button top-left
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
        print("Opening settings dialog")
        # Temporarily release keyboard so dialog is fully interactive
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
        self._virtual_rect = get_virtual_geometry()
        self.setGeometry(self._virtual_rect)
        self._dragging = False
        self._start = QPoint()
        self._end = QPoint()
        # Show as a normal top-level window covering the virtual desktop,
        # not in FullScreen mode. This avoids WM hiding the taskbar/dock.
        self.show()
        self.raise_()
        self.activateWindow()
        # Ensure we receive input immediately even if the WM requires click-to-focus
        try:
            self.grabKeyboard()
        except Exception:
            pass
        self.setFocus(Qt.MouseFocusReason)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.RightButton:
            self.close()
            return
        if event.button() == Qt.LeftButton:
            # If clicking on the settings button, trigger it and do not start selection
            if self.settings_button.geometry().contains(event.pos()):
                self.settings_button.click()
                return
            self._dragging = True
            self._start = event.globalPos()
            self._end = self._start
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self._dragging:
            return
        self._end = event.globalPos()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
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
        self._capture_and_copy(capture_rect)
        self.close()

    def _capture_and_copy(self, capture_rect: QRect) -> None:
        if capture_rect.width() <= 1 or capture_rect.height() <= 1:
            return
        full = grab_full_desktop_pixmap()
        if full is None or full.isNull():
            return
        bounded = capture_rect.intersected(QRect(QPoint(0, 0), full.size()))
        if bounded.isEmpty():
            return
        cropped = full.copy(bounded)
        QGuiApplication.clipboard().setPixmap(cropped)

    def paintEvent(self, _event) -> None:
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
        try:
            self.closed.emit()
        finally:
            try:
                self.releaseKeyboard()
            except Exception:
                pass
            super().closeEvent(event)


class HotkeyBridge(QObject):
    hotkeyPressed = pyqtSignal()


class Controller(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.overlay = SelectionOverlay()

    def show_overlay(self) -> None:
        self.overlay.begin()


def start_hotkey_listener(bridge: HotkeyBridge) -> keyboard.GlobalHotKeys:
    def on_activate():
        bridge.hotkeyPressed.emit()

    listener = keyboard.GlobalHotKeys({
        '<cmd>+<shift>+c': on_activate,
    })
    # Run in this thread; caller will start it in a thread
    return listener


def main() -> int:
    app = QApplication(sys.argv)
    # Allow Ctrl+C to quit the Qt loop cleanly
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    pump = QTimer()
    pump.setInterval(100)
    pump.timeout.connect(lambda: None)
    pump.start()

    controller = Controller()
    bridge = HotkeyBridge()
    bridge.hotkeyPressed.connect(controller.show_overlay)

    listener = start_hotkey_listener(bridge)
    t = threading.Thread(target=listener.run, daemon=True)
    t.start()

    print("Listening for Super+Shift+C ...")
    code = app.exec_()

    try:
        listener.stop()
    except Exception:
        pass
    return code


if __name__ == "__main__":
    raise SystemExit(main())
