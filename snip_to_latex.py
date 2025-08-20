#!/usr/bin/env python3
import sys
import signal
import threading
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

# Use modular implementations
from sniptolatex.controller import Controller as AppController
from sniptolatex.hotkeys import (
    HotkeyBridge as AppHotkeyBridge,
    start_hotkey_listener as app_start_hotkey_listener,
)

def main() -> int:
    app = QApplication(sys.argv)
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

    print("Listening for Super+Shift+C ...")
    code = app.exec_()

    try:
        listener.stop()
    except Exception:
        pass
    return code


if __name__ == "__main__":
    raise SystemExit(main())
