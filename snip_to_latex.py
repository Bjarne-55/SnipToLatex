#!/usr/bin/env python3
import sys
import signal
import threading
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QColor

# Use modular implementations
from sniptolatex.controller import Controller as AppController
from sniptolatex.hotkeys import (
    HotkeyBridge as AppHotkeyBridge,
    start_hotkey_listener as app_start_hotkey_listener,
)

def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Allow Ctrl+C to quit the Qt loop cleanly
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    pump = QTimer()
    pump.setInterval(100)
    pump.timeout.connect(lambda: None)
    pump.start()

    controller = AppController()
    bridge = AppHotkeyBridge()
    bridge.hotkeyPressed.connect(controller.show_overlay)

    listener = app_start_hotkey_listener(bridge)
    t = threading.Thread(target=listener.run, daemon=True)
    t.start()

    #from sniptolatex.toast import Toast
    #toast = Toast()
    #toast.show_loading()

    # Add a tray icon so the app can run headless without a console window
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray = QSystemTrayIcon()
        # Minimal in-memory icon so the tray actually shows up on Windows
        pix = QPixmap(16, 16)
        pix.fill(QColor(0, 153, 255))
        tray.setIcon(QIcon(pix))
        # Simple context menu with Quit
        menu = QMenu()
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(app.quit)
        menu.addAction(quit_action)
        tray.setContextMenu(menu)
        tray.setToolTip("SnipToLatex: Press Win+Shift+C")
        tray.show()
    print("Listening for Super+Shift+C ...")
    code = app.exec_()

    try:
        listener.stop()
    except Exception:
        pass
    return code


if __name__ == "__main__":
    raise SystemExit(main())
