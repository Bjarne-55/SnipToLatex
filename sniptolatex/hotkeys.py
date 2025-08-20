"""Global hotkey bridge using pynput."""

from pynput import keyboard
from PyQt5.QtCore import QObject, pyqtSignal


class HotkeyBridge(QObject):
    """Qt signal bridge to trigger overlay from a global hotkey.

    Attributes:
        hotkeyPressed (pyqtSignal): Emitted when the configured hotkey is pressed.
    """
    hotkeyPressed = pyqtSignal()


def start_hotkey_listener(bridge: HotkeyBridge) -> keyboard.GlobalHotKeys:
    """Create a non-started pynput listener bound to the signal bridge.

    Args:
        bridge (HotkeyBridge): Signal bridge to emit when the hotkey activates.

    Returns:
        keyboard.GlobalHotKeys: A configured pynput listener (not started).

    Raises:
        None.
    """
    def on_activate():
        bridge.hotkeyPressed.emit()

    listener = keyboard.GlobalHotKeys({
        '<cmd>+<shift>+c': on_activate,
    })
    return listener


