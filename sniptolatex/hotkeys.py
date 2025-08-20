from pynput import keyboard
from PyQt5.QtCore import QObject, pyqtSignal


class HotkeyBridge(QObject):
    hotkeyPressed = pyqtSignal()


def start_hotkey_listener(bridge: HotkeyBridge) -> keyboard.GlobalHotKeys:
    def on_activate():
        bridge.hotkeyPressed.emit()

    listener = keyboard.GlobalHotKeys({
        '<cmd>+<shift>+c': on_activate,
    })
    return listener


