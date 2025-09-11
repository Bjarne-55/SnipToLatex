"""Settings dialog for SnipToLatex (PyQt6).

This dialog presents a modern, card-based UI to choose the active model,
manage the API key, and edit default prompts. The layout and visuals follow
the design in ``DesignTemplates/SettingsMenu`` and use an external QSS theme.
"""

from typing import Optional
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QTextOption, QTextCursor
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
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QButtonGroup
from pathlib import Path

from ..config import (
    get_selected_model,
    set_selected_model,
    read_model_settings,
    write_model_settings,
)
from .theme import load_stylesheet


class SettingsDialog(QDialog):
    """Full settings dialog with a modern, minimal design.

    Attributes:
        MODELS: Available model labels and their internal values.
        txt_key: API key input field.
        txt_prompt: Prompt editor text area.
        btn_undo: Undo action button for the prompt editor.
        btn_redo: Redo action button for the prompt editor.
        btn_restore: Restore last saved prompt button.
        btn_delete: Reset prompt to the default template button.
        _segment_group: Button group for segmented model selector.
        _segment_buttons: Mapping of model value to its toggle button.
        _lbl_key_for: Small label describing API key target model.
        _lbl_prompt_for: Small label describing prompt target model.
        _save_indicator: Small "Updated" label flashed on save.
        _eye_icon: Icon for showing the API key.
        _eye_off_icon: Icon for hiding the API key.
        _can_undo: Tracks whether undo is available in the prompt editor.
        _can_redo: Tracks whether redo is available in the prompt editor.
    """

    MODELS = [
        ("Gemini", "gemini"),
        ("ChatGPT", "chatgpt"),
        ("Claude", "claude"),
    ]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the dialog and wire up the UI.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(880, 620)
        self._build_ui()
        self._load_initial_values()

    def _build_ui(self) -> None:
        """Build the dialog UI by composing sections.

        This wires up widgets, signals, and initial styles. The method is
        intentionally shallow by delegating to section builders for clarity.
        """
        self._apply_stylesheet()

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        self._build_header(root)
        self._build_model_card(root)
        self._build_api_key_card(root)
        self._build_prompt_editor(root)
        self._build_footer(root)

        # Ensure all buttons use the pointing-hand cursor on hover
        self._apply_pointer_cursor()

        # Initialize undo/redo buttons state
        self._can_undo = False
        self._can_redo = False
        self._update_undo_state(False)
        self._update_redo_state(False)

    def _apply_stylesheet(self) -> None:
        """Apply the external QSS theme to the dialog.

        Loads the stylesheet via the shared theme loader to resolve color tokens.
        """
        self.setStyleSheet(load_stylesheet("settings_dialog"))

    def _build_header(self, root: QVBoxLayout) -> None:
        """Create the header card with logo, title and save indicator.

        Args:
            root: The root layout to append the header to.
        """
        header = QFrame(self)
        header.setObjectName("header")
        header_l = QHBoxLayout(header)
        header_l.setContentsMargins(12, 10, 12, 10)
        header_l.setSpacing(12)

        logo = QLabel("⚙", header)
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

    def _build_model_card(self, root: QVBoxLayout) -> None:
        """Create the model selection card with segmented buttons.

        Args:
            root: The root layout to append the model card to.
        """
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
        self._segment_buttons: dict[str, QPushButton] = {}
        for label, value in self.MODELS:
            btn = QPushButton(label, segmented)
            btn.setCheckable(True)
            btn.clicked.connect(self._on_segmented_changed)
            self._segment_group.addButton(btn)
            self._segment_buttons[value] = btn
            seg_l.addWidget(btn)
        v_model.addWidget(segmented)
        root.addWidget(card_model)

    def _build_api_key_card(self, root: QVBoxLayout) -> None:
        """Create the API key card with show/hide toggle.

        Args:
            root: The root layout to append the API key card to.
        """
        card_key = QFrame(self)
        card_key.setObjectName("card")
        col_key = QVBoxLayout(card_key)
        col_key.setContentsMargins(12, 12, 12, 12)
        col_key.setSpacing(6)

        lbl_key = QLabel("API Key", card_key)
        self.txt_key = QLineEdit(card_key)
        self.txt_key.setPlaceholderText("Enter API key for selected model")
        self.txt_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_key.setFixedHeight(36)

        # Label: Key for <Model>
        self._lbl_key_for = QLabel("Key for Model", card_key)
        self._lbl_key_for.setObjectName("muted")

        # Show/Hide button (icon-only like template)
        self._btn_toggle_key = QPushButton("", card_key)
        self._btn_toggle_key.setObjectName("iconButton")
        self._btn_toggle_key.setToolTip("Show/Hide API key")
        self._eye_icon = self._load_icon("eye.svg")
        self._eye_off_icon = self._load_icon("eye-off.svg")
        if not self._eye_icon.isNull():
            self._btn_toggle_key.setIcon(self._eye_icon)
        self._btn_toggle_key.clicked.connect(self._toggle_key_visibility)

        row_key = QHBoxLayout()
        row_key.setSpacing(8)
        row_key.addWidget(self.txt_key, 1)
        row_key.addWidget(self._btn_toggle_key, 0)

        col_key.addWidget(lbl_key)
        col_key.addWidget(self._lbl_key_for)
        col_key.addLayout(row_key)
        root.addWidget(card_key)

    def _build_prompt_editor(self, root: QVBoxLayout) -> None:
        """Create the prompt editor card and toolbar.

        Args:
            root: The root layout to append the prompt editor to.
        """
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

        # Toolbar: left label and right action buttons
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self._lbl_prompt_for = QLabel("Editing prompt for Model", prompt_card)
        self._lbl_prompt_for.setObjectName("muted")
        toolbar.addWidget(self._lbl_prompt_for)
        toolbar.addStretch(1)

        self.btn_undo = self._make_icon_button(
            parent=prompt_card,
            tooltip="Undo",
            icon_name="undo.svg",
            on_click=self._on_undo,
        )
        toolbar.addWidget(self.btn_undo)

        self.btn_redo = self._make_icon_button(
            parent=prompt_card,
            tooltip="Redo",
            icon_name="redo.svg",
            on_click=self._on_redo,
        )
        toolbar.addWidget(self.btn_redo)

        self.btn_restore = self._make_icon_button(
            parent=prompt_card,
            tooltip="Restore last saved prompt",
            icon_name="restore.svg",
            on_click=self._restore_last_saved,
        )
        toolbar.addWidget(self.btn_restore)

        self.btn_delete = self._make_icon_button(
            parent=prompt_card,
            tooltip="Replace with default prompt",
            icon_name="trash.svg",
            on_click=self._reset_prompt_to_default,
        )
        toolbar.addWidget(self.btn_delete)
        prompt_v.addLayout(toolbar)

        self.txt_prompt = QPlainTextEdit(prompt_card)
        self.txt_prompt.setPlaceholderText("Edit the prompt sent to the model...")
        self.txt_prompt.setTabChangesFocus(False)
        # Wrap lines to avoid horizontal scrolling
        self.txt_prompt.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.txt_prompt.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.txt_prompt.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.txt_prompt.setUndoRedoEnabled(True)
        # Keep icon buttons in sync with undo/redo availability and cursor/tooltips
        self.txt_prompt.undoAvailable.connect(self._update_undo_state)
        self.txt_prompt.redoAvailable.connect(self._update_redo_state)
        prompt_v.addWidget(self.txt_prompt, 1)
        root.addWidget(prompt_card, 1)

    def _build_footer(self, root: QVBoxLayout) -> None:
        """Create the footer with Cancel/Save buttons.

        Args:
            root: The root layout to append the footer to.
        """
        footer = QFrame(self)
        footer.setObjectName("footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 8, 0, 0)
        footer_layout.addStretch(1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save,
            footer,
        )
        buttons.setOrientation(Qt.Orientation.Horizontal)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        footer_layout.addWidget(buttons, 0)
        root.addWidget(footer)

        # Style the autogenerated buttons
        btn_save = buttons.button(QDialogButtonBox.StandardButton.Save)
        if btn_save is not None:
            btn_save.setObjectName("primary")
            btn_save.setIcon(QIcon())
            btn_save.setText("Save")
            btn_save.setAutoDefault(False)
        btn_cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if btn_cancel is not None:
            btn_cancel.setObjectName("ghost")
            btn_cancel.setIcon(QIcon())
            btn_cancel.setText("Cancel")
            btn_cancel.setAutoDefault(False)

    def _make_icon_button(self, parent: QWidget, tooltip: str, icon_name: str, on_click) -> QPushButton:
        """Create a standardized icon-only button.

        Args:
            parent: Parent widget for the button.
            tooltip: Tooltip text.
            icon_name: File name of the icon in assets/icons.
            on_click: Callable slot to connect to the clicked signal.

        Returns:
            QPushButton: The configured icon-only button.
        """
        btn = QPushButton("", parent)
        btn.setObjectName("iconButton")
        btn.setToolTip(tooltip)
        icon = self._load_icon(icon_name)
        if not icon.isNull():
            btn.setIcon(icon)
        btn.clicked.connect(on_click)
        return btn

    def _apply_pointer_cursor(self) -> None:
        """Set pointing-hand cursor for all buttons in the dialog."""
        for btn in self.findChildren(QPushButton):
            try:
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
            except Exception:
                pass

    def _icon_path(self, name: str) -> Path:
        """Build absolute path to an icon asset.

        Args:
            name: Icon file name (e.g., ``"eye.svg"``).

        Returns:
            Path: Resolved path to the icon.
        """
        return Path(__file__).parent / "assets" / "icons" / name

    def _load_icon(self, name: str) -> QIcon:
        """Safely load an icon.

        Args:
            name: Icon file name.

        Returns:
            QIcon: The loaded icon or an empty icon if loading fails.
        """
        try:
            path = self._icon_path(name)
            return QIcon(str(path))
        except Exception:
            return QIcon()

    def _default_prompt_for(self, model: str) -> str:
        """Get the shipped default prompt text for a model.

        Args:
            model: Internal model value (e.g., ``"gemini"`` or ``"chatgpt"``).

        Returns:
            str: Prompt contents; empty string if unavailable.
        """
        name = "chatgpt_image_to_latex.txt" if model == "chatgpt" else "gemini_image_to_latex.txt"
        # ui/ -> go up to package root to reach ai/prompts
        path = Path(__file__).resolve().parent.parent / "ai" / "prompts" / name
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""

    def _load_initial_values(self) -> None:
        """Initialize model selection and load persisted values."""
        model = get_selected_model()
        # Select segmented button
        value = model if model in (v for _, v in self.MODELS) else "gemini"
        if value in self._segment_buttons:
            self._segment_buttons[value].setChecked(True)
        self._on_segmented_changed()
        self._load_values_for_model(value)
        # Reset undo/redo state after loading content
        self._update_undo_state(False)
        self._update_redo_state(False)

    def _load_values_for_model(self, model: str) -> None:
        """Populate inputs with persisted settings for a given model.

        Args:
            model: Internal model value.
        """
        cfg = read_model_settings(model)
        self.txt_key.setText(cfg.get("api_key") or "")

        # Load stored prompt or default prompt
        stored = cfg.get("prompt")
        raw = stored if (stored is not None and len(stored) > 0) else self._default_prompt_for(model)
        self.txt_prompt.setPlainText(raw)

    def _reset_prompt_to_default(self) -> None:
        """Replace the editor content with the shipped default prompt.

        Use an undoable edit so the user can undo this action.
        """
        model = self.current_model()
        self._set_prompt_text_undoable(self._default_prompt_for(model))

    def _restore_last_saved(self) -> None:
        """Restore the last saved prompt for the selected model.

        Falls back to the shipped default if nothing was saved.
        """
        model = self.current_model()
        cfg = read_model_settings(model)
        stored = cfg.get("prompt")
        if stored is None or len(stored) == 0:
            stored = self._default_prompt_for(model)
        # Perform as an undoable replace so user can undo Restore.
        self._set_prompt_text_undoable(stored)

    def _set_prompt_text_undoable(self, text: str) -> None:
        """Set prompt editor contents as a single undoable operation.

        Programmatic setPlainText clears the undo stack. To allow users to
        undo actions like Restore/Delete, we replace the entire document
        using a QTextCursor edit block which becomes one undo step.
        """
        try:
            cursor = self.txt_prompt.textCursor()
            cursor.beginEditBlock()
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.insertText(text)
            cursor.endEditBlock()
        except Exception:
            # Fallback if anything goes wrong
            self.txt_prompt.setPlainText(text)

    def _on_segmented_changed(self) -> None:
        """Update context labels and reload values when the model changes."""
        model = self.current_model()
        # Update context labels
        name_label = self.model_label(model)
        self._lbl_key_for.setText(f"Key for {name_label}")
        self._lbl_prompt_for.setText(f"Editing prompt for {name_label}")
        self._load_values_for_model(model)

    def current_model(self) -> str:
        """Return the current model value selected in the segmented control.

        Returns:
            str: Internal model value (e.g., ``"gemini"``).
        """
        for label, value in self.MODELS:
            btn = self._segment_buttons[value]
            if btn.isChecked():
                return value
        return "gemini"

    def model_label(self, value: str) -> str:
        """Get the human-readable label for a model value.

        Args:
            value: Internal model value.

        Returns:
            str: Display label for the model.
        """
        for label, v in self.MODELS:
            if v == value:
                return label
        return "Gemini"

    def _toggle_key_visibility(self) -> None:
        """Toggle API key visibility and update the eye icon accordingly."""
        if self.txt_key.echoMode() == QLineEdit.EchoMode.Password:
            self.txt_key.setEchoMode(QLineEdit.EchoMode.Normal)
            if not self._eye_off_icon.isNull():
                self._btn_toggle_key.setIcon(self._eye_off_icon)
        else:
            self.txt_key.setEchoMode(QLineEdit.EchoMode.Password)
            if not self._eye_icon.isNull():
                self._btn_toggle_key.setIcon(self._eye_icon)

    def _on_undo(self) -> None:
        """Invoke undo in the prompt editor or beep if unavailable."""
        try:
            if getattr(self, "_can_undo", False):
                self.txt_prompt.undo()
            else:
                QApplication.beep()
        except Exception:
            pass

    def _on_redo(self) -> None:
        """Invoke redo in the prompt editor or beep if unavailable."""
        try:
            if getattr(self, "_can_redo", False):
                self.txt_prompt.redo()
            else:
                QApplication.beep()
        except Exception:
            pass

    def _set_icon_btn_cursor(self, btn: QPushButton, enabled: bool) -> None:
        """Adjust cursor, tooltip and inactive state on an icon button.

        Args:
            btn: Target button.
            enabled: If False, indicates no action is available.
        """
        try:
            btn.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ForbiddenCursor)
            # Update tooltip hint
            if btn is self.btn_undo:
                btn.setToolTip("Undo" if enabled else "Nothing to undo")
            elif btn is self.btn_redo:
                btn.setToolTip("Redo" if enabled else "Nothing to redo")
            # reflect inactive state for styling and hover suppression
            btn.setProperty("inactive", not enabled)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()
        except Exception:
            pass

    def _update_undo_state(self, available: bool) -> None:
        """Track and reflect undo availability in the toolbar.

        Args:
            available: Whether undo is currently available.
        """
        self._can_undo = bool(available)
        self._set_icon_btn_cursor(self.btn_undo, self._can_undo)

    def _update_redo_state(self, available: bool) -> None:
        """Track and reflect redo availability in the toolbar.

        Args:
            available: Whether redo is currently available.
        """
        self._can_redo = bool(available)
        self._set_icon_btn_cursor(self.btn_redo, self._can_redo)

    def _save(self) -> None:
        """Persist current model, API key and prompt, then close the dialog."""
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
            QTimer.singleShot(1100, lambda: self._save_indicator.setVisible(False))
        self.accept()
