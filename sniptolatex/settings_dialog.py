from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Placeholder settings", self))
        layout.addWidget(QLabel("- Option A: ...", self))
        layout.addWidget(QLabel("- Option B: ...", self))
        self.resize(320, 200)


