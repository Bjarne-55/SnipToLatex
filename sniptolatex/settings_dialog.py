"""Modern Settings dialog for SnipToLatex (PyQt6).

Design follows the dark, card-based layout in DesignTemplates/SettingsMenu,
with a segmented model selector, API key field with show/hide,
and a prompt editor with reset.
"""

from typing import Optional
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QDialogButtonBox,
    QWidget,
    QPushButton,
    QFrame,
)
from PyQt6.QtWidgets import QButtonGroup
from pathlib import Path

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
        ("ChatGPT", "chatgpt"),
        ("Claude", "claude"),
    ]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(880, 620)
        self._build_ui()
        self._load_initial_values()

    def _build_ui(self) -> None:
        # Modern, clean stylesheet
        self.setStyleSheet(
            """
            QDialog { background: #0b0f12; color: #e6edf3; }
            QLabel { color: #e6edf3; font-size: 14px; }

            /* Cards */
            QFrame#header {
                background-color: rgba(255,255,255,0.02);
                border: 1px solid #223142;
                border-radius: 14px;
                padding: 16px 18px;
            }
            QFrame#card {
                background-color: rgba(255,255,255,0.02);
                border: 1px solid #223142;
                border-radius: 14px;
                padding: 16px;
            }

            /* Inputs */
            QLineEdit, QPlainTextEdit {
                font-size: 14px;
                color: #e6edf3;
                background: #10161b;
                border: 1px solid #223142;
                border-radius: 10px;
                padding: 10px 12px;
            }
            QLineEdit:focus, QPlainTextEdit:focus {
                border: 1px solid #a48bff;
            }
            QPlainTextEdit { font-family: Consolas, "SF Mono", Menlo, Monaco, "Courier New", monospace; }

            /* Segmented */
            #segmented { background: #10161b; border: 1px solid #223142; border-radius: 12px; padding: 4px; }
            #segmented QPushButton {
                background: transparent; color: #e6edf3; border: none; border-radius: 10px; padding: 10px 12px; min-width: 110px;
            }
            #segmented QPushButton:hover { background: rgba(255,255,255,0.04); }
            #segmented QPushButton:checked {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 rgba(109,214,255,0.14), stop:1 rgba(164,139,255,0.14));
                border: 1px solid rgba(164,139,255,0.35);
            }

            /* Footer + Buttons */
            QFrame#footer { border-top: 1px solid #223142; padding-top: 12px; margin-top: 4px; }
            QDialogButtonBox QPushButton {
                min-height: 36px; min-width: 96px;
                padding: 10px 16px; border-radius: 12px; font-weight: 600;
                border: 1px solid #223142; background: rgba(255,255,255,0.03); color: #e6edf3;
            }
            QDialogButtonBox QPushButton:hover { background: rgba(255,255,255,0.06); }
            QPushButton#primary { border: none; background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #6dd6ff, stop:1 #a48bff); color: #0b0f12; font-weight: 700; }
            /* Ghost buttons for subtle actions (dashed border like Design_Menu) */
            QPushButton#ghost {
                background: transparent;
                border: 1px dashed #223142;
                border-radius: 10px;
                padding: 6px 12px;
                color: #e6edf3;
            }
            QPushButton#ghost:hover { background: rgba(255,255,255,0.03); }
            QPushButton#ghost:focus { border: 1px dashed #6dd6ff; }

            /* Muted labels */
            #muted { color: #8a97a5; font-size: 13px; }
            #title { font-size: 22px; font-weight: 700; margin: 0; }
            #logo { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #6dd6ff, stop:1 #a48bff); color: #0b0f12; border-radius: 10px; }
            #promptHeader QLabel { color: #e6edf3; }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        # Header card (logo + title)
        header = QFrame(self)
        header.setObjectName("header")
        header_l = QHBoxLayout(header)
        header_l.setContentsMargins(12, 10, 12, 10)
        header_l.setSpacing(12)
        logo = QLabel("∑", header)
        logo.setObjectName("logo")
        logo.setFixedSize(36, 36)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_col = QVBoxLayout()
        title = QLabel("Settings", header)
        title.setObjectName("title")
        subtitle = QLabel("Choose model, set API key, and edit prompts.", header)
        subtitle.setObjectName("muted")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_l.addWidget(logo)
        header_l.addLayout(title_col)
        header_l.addStretch(1)
        self._save_indicator = QLabel("Updated", header)
        self._save_indicator.setObjectName("muted")
        self._save_indicator.setVisible(False)
        header_l.addWidget(self._save_indicator)
        root.addWidget(header)

        # Model card with segmented control
        card_model = QFrame(self)
        card_model.setObjectName("card")
        v_model = QVBoxLayout(card_model)
        v_model.setContentsMargins(8, 6, 8, 6)
        v_model.setSpacing(10)
        header_model = QVBoxLayout()
        h2 = QLabel("Model", card_model)
        p = QLabel("Choose which LLM to use", card_model)
        p.setObjectName("muted")
        header_model.addWidget(h2)
        header_model.addWidget(p)
        v_model.addLayout(header_model)

        segmented = QFrame(card_model)
        segmented.setObjectName("segmented")
        seg_l = QHBoxLayout(segmented)
        seg_l.setContentsMargins(4, 4, 4, 4)
        seg_l.setSpacing(6)
        self._segment_group = QButtonGroup(self)
        self._segment_group.setExclusive(True)
        self._segment_buttons = {}
        for label, value in self.MODELS:
            btn = QPushButton(label, segmented)
            btn.setCheckable(True)
            btn.clicked.connect(self._on_segmented_changed)
            self._segment_group.addButton(btn)
            self._segment_buttons[value] = btn
            seg_l.addWidget(btn)
        v_model.addWidget(segmented)
        root.addWidget(card_model)

        # API key card
        card_key = QFrame(self)
        card_key.setObjectName("card")
        col_key = QVBoxLayout(card_key)
        col_key.setContentsMargins(12, 12, 12, 12)
        col_key.setSpacing(6)
        lbl_key = QLabel("API Key", card_key)
        self.txt_key = QLineEdit(card_key)
        self.txt_key.setPlaceholderText("Enter API key for selected model")
        self.txt_key.setEchoMode(QLineEdit.EchoMode.Password)
        # Label: Key for <Model>
        self._lbl_key_for = QLabel("Key for Model", card_key)
        self._lbl_key_for.setObjectName("muted")
        # Show/Hide button
        self._btn_toggle_key = QPushButton("Show", card_key)
        self._btn_toggle_key.setObjectName("ghost")
        self._btn_toggle_key.setFixedHeight(self.txt_key.sizeHint().height())
        self._btn_toggle_key.setMinimumWidth(72)
        self._btn_toggle_key.clicked.connect(self._toggle_key_visibility)
        row_key = QHBoxLayout()
        row_key.setSpacing(8)
        row_key.addWidget(self.txt_key, 1)
        row_key.addWidget(self._btn_toggle_key, 0)
        col_key.addWidget(lbl_key)
        col_key.addWidget(self._lbl_key_for)
        col_key.addLayout(row_key)
        root.addWidget(card_key)
        # Ensure the toggle button matches the rendered line edit height
        QTimer.singleShot(0, self._sync_toggle_btn_height)

        # (Personalization section removed)

        # Prompt editor
        # Prompt header with reset button
        prompt_card = QFrame(self)
        prompt_card.setObjectName("card")
        prompt_v = QVBoxLayout(prompt_card)
        prompt_v.setContentsMargins(12, 12, 12, 12)
        prompt_v.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        header_row.setObjectName("promptHeader")
        lbl_prompt = QLabel("Default Prompt", prompt_card)
        header_row.addWidget(lbl_prompt)
        header_row.addStretch(1)
        prompt_v.addLayout(header_row)

        # Toolbar: left label and right reset button
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self._lbl_prompt_for = QLabel("Editing prompt for Model", prompt_card)
        self._lbl_prompt_for.setObjectName("muted")
        toolbar.addWidget(self._lbl_prompt_for)
        toolbar.addStretch(1)
        self.btn_reset = QPushButton("Reset to default", prompt_card)
        self.btn_reset.setObjectName("ghost")
        self.btn_reset.clicked.connect(self._reset_prompt_to_default)
        toolbar.addWidget(self.btn_reset)
        prompt_v.addLayout(toolbar)

        self.txt_prompt = QPlainTextEdit(prompt_card)
        self.txt_prompt.setPlaceholderText("Edit the prompt sent to the model...")
        self.txt_prompt.setTabChangesFocus(False)
        self.txt_prompt.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        prompt_v.addWidget(self.txt_prompt, 1)
        root.addWidget(prompt_card, 1)

        # Footer with dialog buttons
        footer = QFrame(self)
        footer.setObjectName("footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 8, 0, 0)
        footer_layout.addStretch(1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save, footer)
        buttons.setOrientation(Qt.Orientation.Horizontal)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        footer_layout.addWidget(buttons, 0)
        root.addWidget(footer)
        # Style the autogenerated buttons
        btn_save = buttons.button(QDialogButtonBox.StandardButton.Save)
        if btn_save is not None:
            btn_save.setObjectName("primary")
            # Remove platform icons and mnemonics to match design
            btn_save.setIcon(QIcon())
            btn_save.setText("Save")
            btn_save.setAutoDefault(False)
        btn_cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if btn_cancel is not None:
            btn_cancel.setObjectName("ghost")
            btn_cancel.setIcon(QIcon())
            btn_cancel.setText("Cancel")
            btn_cancel.setAutoDefault(False)

        # Ensure all buttons use the pointing-hand cursor on hover
        self._apply_pointer_cursor()

    def _apply_pointer_cursor(self) -> None:
        """Set pointing-hand cursor for all buttons in the dialog."""
        for btn in self.findChildren(QPushButton):
            try:
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
            except Exception:
                pass

    def _sync_toggle_btn_height(self) -> None:
        try:
            h = max(self.txt_key.height(), self.txt_key.sizeHint().height())
            if h > 0:
                self._btn_toggle_key.setFixedHeight(h)
        except Exception:
            pass

    def _default_prompt_for(self, model: str) -> str:
        name = "chatgpt_image_to_latex.txt" if model == "chatgpt" else "gemini_image_to_latex.txt"
        path = Path(__file__).parent / "ai" / "prompts" / name
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""

    def _load_initial_values(self) -> None:
        model = get_selected_model()
        # Select segmented button
        value = model if model in (v for _, v in self.MODELS) else "gemini"
        if value in self._segment_buttons:
            self._segment_buttons[value].setChecked(True)
        self._on_segmented_changed()
        self._load_values_for_model(value)

    def _load_values_for_model(self, model: str) -> None:
        cfg = read_model_settings(model)
        self.txt_key.setText(cfg.get("api_key") or "")

        # Load stored prompt or default prompt
        stored = cfg.get("prompt")
        raw = stored if (stored is not None and len(stored) > 0) else self._default_prompt_for(model)
        self.txt_prompt.setPlainText(raw)

    def _reset_prompt_to_default(self) -> None:
        model = self.current_model()
        self.txt_prompt.setPlainText(self._default_prompt_for(model))

    def _on_segmented_changed(self) -> None:
        model = self.current_model()
        # Update context labels
        name_label = self.model_label(model)
        self._lbl_key_for.setText(f"Key for {name_label}")
        self._lbl_prompt_for.setText(f"Editing prompt for {name_label}")
        self._load_values_for_model(model)

    def current_model(self) -> str:
        for label, value in self.MODELS:
            btn = self._segment_buttons[value]
            if btn.isChecked():
                return value
        return "gemini"

    def model_label(self, value: str) -> str:
        for label, v in self.MODELS:
            if v == value:
                return label
        return "Gemini"

    def _toggle_key_visibility(self) -> None:
        if self.txt_key.echoMode() == QLineEdit.EchoMode.Password:
            self.txt_key.setEchoMode(QLineEdit.EchoMode.Normal)
            self._btn_toggle_key.setText("Hide")
        else:
            self.txt_key.setEchoMode(QLineEdit.EchoMode.Password)
            self._btn_toggle_key.setText("Show")

    def _save(self) -> None:
        model = self.current_model()
        # Persist selected model
        set_selected_model(model)
        # Persist per-model settings
        write_model_settings(
            model,
            api_key=self.txt_key.text().strip(),
            prompt=self.txt_prompt.toPlainText(),
        )
        # Flash save indicator
        if hasattr(self, "_save_indicator"):
            self._save_indicator.setVisible(True)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1100, lambda: self._save_indicator.setVisible(False))
        self.accept()
