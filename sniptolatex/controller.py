"""Thin controller to show the overlay on demand (PyQt6)."""

from PyQt6.QtCore import QObject

from .ui.overlay import SelectionOverlay


class Controller(QObject):
    """Application controller coordinating the selection overlay lifecycle.

    Attributes:
        overlay (SelectionOverlay): The selection UI managed by this controller.
    """

    def __init__(self) -> None:
        super().__init__()
        self.overlay = SelectionOverlay()

    def show_overlay(self) -> None:
        """Display the overlay and start selection.

        Returns:
            None

        Raises:
            None.
        """
        self.overlay.begin()
