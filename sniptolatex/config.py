"""Configuration utilities for SnipToLatex.

Creates and reads a simple INI file so users can provide their API key
without setting environment variables.
"""

import os
from configparser import ConfigParser
from typing import Dict, Optional


_APP_DIR_NAME = "SnipToLatex"
_SECTION = "sniptolatex"

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


def read_config() -> Dict[str, Optional[str]]:
    """Read configuration values from the INI file.

    Returns a dict with keys: 'api_key', 'model'. Missing keys map to None.
    """
    parser = ConfigParser()
    parser.read(get_config_path(), encoding="utf-8")
    api_key = parser.get(_SECTION, "api_key", fallback=None)
    model = parser.get(_SECTION, "model", fallback=None)
    return {"api_key": api_key, "model": model}


