"""Modern Settings dialog for SnipToLatex.

Features:
- Model selector (Gemini, ChatGPT placeholder)
- Model-specific API key
- Personalization: Force no bold (\mathbf)
- Prompt editor with save support
"""

from typing import Optional
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QPlainTextEdit,
    QDialogButtonBox,
    QWidget,
)

from .config import (
    get_selected_model,
    set_selected_model,
    read_model_settings,
    write_model_settings,
)
from .ai.gemini import GeminiRequest
from .ai.chatgpt import ChatGPTRequest


class SettingsDialog(QDialog):
    """Full settings dialog with a modern, minimal design."""

    MODELS = [
        ("Gemini", "gemini"),
        ("ChatGPT (placeholder)", "chatgpt"),
    ]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(700, 540)
        self._build_ui()
        self._load_initial_values()

    def _build_ui(self) -> None:
        self.setStyleSheet(
            """
            QDialog { background: #fafafa; }
            QLabel { color: #222; font-size: 14px; }
            QLineEdit, QPlainTextEdit, QComboBox { font-size: 14px; }
            QLineEdit, QPlainTextEdit, QComboBox { background: #fff; border: 1px solid #cfcfcf; border-radius: 6px; padding: 6px; }
            QCheckBox { font-size: 14px; }
            #title { font-size: 18px; font-weight: 600; margin-bottom: 6px; }
            #subtitle { color: #666; margin-bottom: 18px; }
            #groupLabel { font-weight: 600; color: #333; }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        title = QLabel("SnipToLatex Settings", self)
        title.setObjectName("title")
        subtitle = QLabel("Choose model, set API key, and edit prompts.", self)
        subtitle.setObjectName("subtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        # Model selector row
        row_model = QHBoxLayout()
        row_model.setSpacing(12)
        lbl_model = QLabel("Model", self)
        lbl_model.setObjectName("groupLabel")
        self.cmb_model = QComboBox(self)
        for label, value in self.MODELS:
            self.cmb_model.addItem(label, value)
        self.cmb_model.currentIndexChanged.connect(self._on_model_changed)
        row_model.addWidget(lbl_model, 0)
        row_model.addWidget(self.cmb_model, 1)
        root.addLayout(row_model)

        # API key row
        row_key = QVBoxLayout()
        lbl_key = QLabel("API Key", self)
        lbl_key.setObjectName("groupLabel")
        self.txt_key = QLineEdit(self)
        self.txt_key.setPlaceholderText("Enter API key for selected model")
        self.txt_key.setEchoMode(QLineEdit.Password)
        row_key.addWidget(lbl_key)
        row_key.addWidget(self.txt_key)
        root.addLayout(row_key)

        # Personalization
        row_personal = QVBoxLayout()
        lbl_personal = QLabel("Personalization", self)
        lbl_personal.setObjectName("groupLabel")
        self.chk_no_bold = QCheckBox("Force no bold (\\mathbf) in output", self)
        row_personal.addWidget(lbl_personal)
        row_personal.addWidget(self.chk_no_bold)
        root.addLayout(row_personal)

        # Prompt editor
        lbl_prompt = QLabel("Prompt", self)
        lbl_prompt.setObjectName("groupLabel")
        self.txt_prompt = QPlainTextEdit(self)
        self.txt_prompt.setPlaceholderText("Edit the prompt sent to the model...")
        self.txt_prompt.setTabChangesFocus(False)
        self.txt_prompt.setLineWrapMode(QPlainTextEdit.NoWrap)
        root.addWidget(lbl_prompt)
        root.addWidget(self.txt_prompt, 1)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _default_prompt_for(self, model: str) -> str:
        if model == "chatgpt":
            return ChatGPTRequest()._read_prompt_from_file()
        return GeminiRequest()._read_prompt_from_file()

    def _load_initial_values(self) -> None:
        model = get_selected_model()
        idx = max(0, self.cmb_model.findData(model))
        self.cmb_model.setCurrentIndex(idx)
        self._load_values_for_model(self.cmb_model.currentData())

    def _load_values_for_model(self, model: str) -> None:
        cfg = read_model_settings(model)
        self.txt_key.setText(cfg.get("api_key") or "")

        force_no_bold = cfg.get("force_no_bold")
        # Default True if not set to preserve existing behavior
        self.chk_no_bold.setChecked(True if force_no_bold is None else (force_no_bold.lower() == "true"))

        # Load prompt override or default prompt
        override = cfg.get("prompt_override")
        raw = override if (override is not None and len(override) > 0) else self._default_prompt_for(model)
        self.txt_prompt.setPlainText(raw)

    def _on_model_changed(self, _idx: int) -> None:
        self._load_values_for_model(self.cmb_model.currentData())

    def _save(self) -> None:
        model = self.cmb_model.currentData()
        # Persist selected model
        set_selected_model(model)
        # Persist per-model settings
        write_model_settings(
            model,
            api_key=self.txt_key.text().strip(),
            prompt_override=self.txt_prompt.toPlainText(),
            force_no_bold=self.chk_no_bold.isChecked(),
        )
        self.accept()


