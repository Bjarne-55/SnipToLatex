"""Configuration utilities for SnipToLatex.

Provides read/write helpers for application- and model-level settings:
 - Selected model name under section ``[sniptolatex]`` key ``model``.
 - Per-model sections named ``[model.<name>]`` with keys:
     - ``api_key``: string
     - ``prompt_override``: string (optional; if absent, default prompt is used)
     - ``force_no_bold``: bool as ``true``/``false`` (optional; defaults to true)
"""

import os
from configparser import ConfigParser
from typing import Dict, Optional


_APP_DIR_NAME = "SnipToLatex"
_SECTION_APP = "sniptolatex"
_SECTION_MODEL_PREFIX = "model."

def get_config_dir() -> str:
    """Return the user-specific configuration directory.

    On Windows, uses %APPDATA% (Roaming). On other OSes, uses XDG_CONFIG_HOME
    or ~/.config.
    """
    if os.name == "nt":
        base = os.getenv("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    else:
        base = os.getenv("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    
    return os.path.join(base, _APP_DIR_NAME)


def get_config_path() -> str:
    return os.path.join(get_config_dir(), "config.ini")


def _ensure_config_dir() -> None:
    os.makedirs(get_config_dir(), exist_ok=True)


def _load_parser() -> ConfigParser:
    parser = ConfigParser()
    parser.read(get_config_path(), encoding="utf-8")
    return parser


def _save_parser(parser: ConfigParser) -> None:
    _ensure_config_dir()
    with open(get_config_path(), "w", encoding="utf-8") as fh:
        parser.write(fh)


def get_selected_model(default: str = "gemini") -> str:
    parser = _load_parser()
    return parser.get(_SECTION_APP, "model", fallback=default)


def set_selected_model(model: str) -> None:
    parser = _load_parser()
    if not parser.has_section(_SECTION_APP):
        parser.add_section(_SECTION_APP)
    parser.set(_SECTION_APP, "model", model)
    _save_parser(parser)


def _model_section(model: str) -> str:
    return f"{_SECTION_MODEL_PREFIX}{model}"


def read_model_settings(model: str) -> Dict[str, Optional[str]]:
    """Return per-model settings dict.

    Keys: 'api_key' (str|None), 'prompt_override' (str|None), 'force_no_bold' (str|None)
    The 'force_no_bold' is returned as 'true'/'false' string or None if unset.
    """
    parser = _load_parser()
    section = _model_section(model)
    api_key = parser.get(section, "api_key", fallback=None)
    prompt_override = parser.get(section, "prompt_override", fallback=None)
    force_no_bold = parser.get(section, "force_no_bold", fallback=None)
    return {
        "api_key": api_key,
        "prompt_override": prompt_override,
        "force_no_bold": force_no_bold,
    }


def write_model_settings(
    model: str,
    *,
    api_key: Optional[str] = None,
    prompt_override: Optional[str] = None,
    force_no_bold: Optional[bool] = None,
) -> None:
    """Persist per-model settings; pass None to leave fields unchanged."""
    parser = _load_parser()
    section = _model_section(model)
    if not parser.has_section(section):
        parser.add_section(section)
    if api_key is not None:
        parser.set(section, "api_key", api_key)
    if prompt_override is not None:
        parser.set(section, "prompt_override", prompt_override)
    if force_no_bold is not None:
        parser.set(section, "force_no_bold", "true" if force_no_bold else "false")
    _save_parser(parser)


