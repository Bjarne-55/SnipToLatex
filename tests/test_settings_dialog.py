import os
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def qapp():
    """Provide a single QApplication instance for all tests (headless)."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PyQt6.QtWidgets import QApplication
    except Exception as e:  # pragma: no cover - import guard
        pytest.skip(f"PyQt6 not available: {e}")
    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture()
def isolated_config_dir(tmp_path, monkeypatch):
    """Isolate config to a temporary directory via XDG/APPDATA env vars.

    sniptolatex.config resolves its dir using XDG_CONFIG_HOME on non-Windows
    and APPDATA on Windows; set both to `tmp_path` so tests never touch user files.
    """
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))
    return tmp_path


def test_settings_save_persists_selected_model_and_values(qapp, isolated_config_dir):
    # Import inside test so env patch is effective
    from sniptolatex.ui.settings_dialog import SettingsDialog
    from sniptolatex.config import get_selected_model, read_model_settings

    dlg = SettingsDialog()

    # Defaults to gemini when no config exists
    assert dlg.current_model() == "gemini"

    # Enter values and save
    dlg.txt_key.setText("GEM-123")
    dlg.txt_prompt.setPlainText("Hello prompt gem")
    dlg._save()

    # Verify config persisted correctly
    assert get_selected_model() == "gemini"
    gem_cfg = read_model_settings("gemini")
    assert gem_cfg["api_key"] == "GEM-123"
    assert gem_cfg["prompt"] == "Hello prompt gem"

    # Unchanged model section should be empty
    chat_cfg = read_model_settings("chatgpt")
    assert chat_cfg["api_key"] is None
    assert chat_cfg["prompt"] is None


def test_settings_loads_values_per_model_and_switches(qapp, isolated_config_dir):
    # Pre-seed config with distinct values for two models
    from sniptolatex.config import (
        write_model_settings,
        set_selected_model,
        read_model_settings,
        get_selected_model,
    )

    write_model_settings("gemini", api_key="G-KEY", prompt="G-PROMPT")
    write_model_settings("chatgpt", api_key="C-KEY", prompt="C-PROMPT")
    set_selected_model("chatgpt")

    from sniptolatex.ui.settings_dialog import SettingsDialog

    dlg = SettingsDialog()

    # Dialog should initialize to selected model and load its values
    assert dlg.current_model() == "chatgpt"
    assert dlg.txt_key.text() == "C-KEY"
    assert dlg.txt_prompt.toPlainText() == "C-PROMPT"

    # Switch to gemini and verify values update from config
    dlg._segment_buttons["gemini"].click()
    assert dlg.current_model() == "gemini"
    assert dlg.txt_key.text() == "G-KEY"
    assert dlg.txt_prompt.toPlainText() == "G-PROMPT"

    # Modify gemini values and save; selected model should persist as gemini
    dlg.txt_key.setText("G-KEY-2")
    dlg.txt_prompt.setPlainText("G-PROMPT-2")
    dlg._save()

    assert get_selected_model() == "gemini"
    g2 = read_model_settings("gemini")
    assert g2["api_key"] == "G-KEY-2"
    assert g2["prompt"] == "G-PROMPT-2"

def test_settings_prompt_buttons(qapp, isolated_config_dir):
    from sniptolatex.config import (
        write_model_settings,
        set_selected_model,
        read_model_settings,
        get_selected_model,
    )
    write_model_settings("gemini", api_key="G-KEY", prompt="G-PROMPT")
    set_selected_model("gemini")

    from sniptolatex.ui.settings_dialog import SettingsDialog

    dlg = SettingsDialog()

    # Dialog should initialize to selected model and load its values
    assert dlg.current_model() == "gemini"
    assert dlg.txt_key.text() == "G-KEY"
    assert dlg.txt_prompt.toPlainText() == "G-PROMPT"
    
    path_default_prompt = Path(__file__).resolve().parent.parent / "sniptolatex" / \
        "ai" / "prompts" / "gemini_image_to_latex.txt"
    default_prompt = path_default_prompt.read_text(encoding="utf-8")

    # Clicking delete resets to the shipped default
    dlg.btn_delete.click()
    assert dlg.txt_prompt.toPlainText() == default_prompt

    # Simulate user edit so it becomes undoable
    from PyQt6.QtTest import QTest
    dlg.txt_prompt.selectAll()
    QTest.keyClicks(dlg.txt_prompt, "G-PROMPT-2")
    qapp.processEvents()

    # undo: default, G-PROMPT
    dlg.btn_undo.click()
    qapp.processEvents()
    assert dlg.txt_prompt.toPlainText() == default_prompt
    dlg.btn_undo.click()
    qapp.processEvents()
    assert dlg.txt_prompt.toPlainText() == "G-PROMPT"

    # Redo: default, then typed text
    dlg.btn_redo.click()
    qapp.processEvents()
    assert dlg.txt_prompt.toPlainText() == default_prompt
    dlg.btn_redo.click()
    qapp.processEvents()
    assert dlg.txt_prompt.toPlainText() == "G-PROMPT-2"

    # Restore button reloads last saved prompt from config
    dlg.btn_restore.click()
    qapp.processEvents()
    assert dlg.txt_prompt.toPlainText() == "G-PROMPT"

    # check undoable
    dlg.btn_undo.click()
    qapp.processEvents()
    assert dlg.txt_prompt.toPlainText() == "G-PROMPT-2"
    dlg.btn_redo.click()
    qapp.processEvents()
    assert dlg.txt_prompt.toPlainText() == "G-PROMPT"

