"""Minimal settings dialog placeholder."""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel


class SettingsDialog(QDialog):
    """Placeholder dialog for future configurable settings.

    Attributes:
        (Qt-managed widgets): Layout and labels composing the dialog UI.
    """

    def __init__(self, parent=None) -> None:
        """Initialize a simple settings dialog with placeholder content.

        Args:
            parent (QWidget|None): Optional parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Settings")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Placeholder settings", self))
        layout.addWidget(QLabel("- Option A: ...", self))
        layout.addWidget(QLabel("- Option B: ...", self))
        self.resize(320, 200)


