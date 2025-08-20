from PyQt5.QtCore import QObject

from .overlay import SelectionOverlay


class Controller(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.overlay = SelectionOverlay()

    def show_overlay(self) -> None:
        self.overlay.begin()


