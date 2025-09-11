from __future__ import annotations

from pathlib import Path
from typing import Dict, Mapping, Optional
import re

from PyQt6.QtGui import QColor


# Centralized color variables for the app. Tokens are referenced in QSS as
# e.g., @fg-text, and replaced at runtime before applying the stylesheet.
DEFAULT_COLORS: Dict[str, str] = {
    # Base palette
    "@bg-base": "#0b0f12",
    "@fg-text": "#e6edf3",
    "@muted-text": "#8a97a5",
    "@border": "#223142",
    "@input-bg": "#10161b",

    # Accents
    "@accent-cyan": "#6dd6ff",
    "@accent-violet": "#a48bff",
    "@ok": "#4ade80",
    "@ok-45": "rgba(74, 222, 128, 0.45)",

    # Whites with alpha (effects)
    "@white-02": "rgba(255,255,255,0.02)",
    "@white-03": "rgba(255,255,255,0.03)",
    "@white-04": "rgba(255,255,255,0.04)",
    "@white-06": "rgba(255,255,255,0.06)",

    # Glow and gradients
    "@glow-purple-12": "rgba(90, 61, 255, 0.12)",
    "@glow-purple-03": "rgba(90, 61, 255, 0.03)",
    "@black-00": "rgba(0, 0, 0, 0.00)",
    "@cyan-14": "rgba(109,214,255,0.14)",
    "@violet-14": "rgba(164,139,255,0.14)",
    "@violet-35": "rgba(164,139,255,0.35)",
}


def _styles_dir() -> Path:
    return Path(__file__).parent / "styles"


def load_stylesheet(name: str, colors: Mapping[str, str] | None = None) -> str:
    """Load a QSS stylesheet by name from ui/styles and resolve tokens.

    Args:
        name: Filename without extension (e.g., "settings_dialog").
        colors: Optional mapping overriding DEFAULT_COLORS.

    Returns:
        str: Resolved QSS stylesheet content.
    """
    path = _styles_dir() / f"{name}.qss"
    raw = path.read_text(encoding="utf-8")
    return resolve_qss(raw, colors)


def resolve_qss(qss: str, colors: Mapping[str, str] | None = None) -> str:
    """Resolve @tokens in a QSS string using the theme palette.

    Replaces longer tokens first to avoid substring collisions (e.g.,
    replacing ``@ok`` before ``@ok-45`` would corrupt the latter).

    Args:
        qss: Raw QSS content with ``@tokens``.
        colors: Optional overrides for the default palette.

    Returns:
        str: QSS with tokens resolved to color values.
    """
    palette = dict(DEFAULT_COLORS)
    if colors:
        palette.update(colors)
    # Replace longer tokens first to avoid partial replacements
    for token in sorted(palette.keys(), key=len, reverse=True):
        qss = qss.replace(token, palette[token])
    return qss


# --------------------------------------------------------------------------------------
# QColor helpers
# --------------------------------------------------------------------------------------

_RGBA_RE = re.compile(r"rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*([0-1]?(?:\.\d+)?)\s*\)", re.IGNORECASE)


def get_QColor(token: str, *, fallback: Optional[str] = None) -> QColor:
    """Return the theme color for ``token`` as a ``QColor``.

    Looks up ``token`` (e.g., "@accent-cyan") in ``DEFAULT_COLORS`` and parses
    its value, supporting both hex ("#RRGGBB") and "rgba(r,g,b,a)" formats.

    Args:
        token: Theme token name (including the leading '@').
        fallback: Optional fallback color string to use if the token is missing
            or invalid. Supports the same formats as above.

    Returns:
        QColor: Parsed color; returns a transparent color if parsing fails.
    """
    raw = DEFAULT_COLORS.get(token)
    if raw is None and fallback is not None:
        raw = fallback
    if raw is None:
        return QColor(0, 0, 0, 0)
    c = get_QColor_hex(raw) if raw.startswith('#') else get_QColor_rgba(raw)
    if not c.isValid() and fallback:
        return get_QColor_hex(fallback) if fallback.startswith('#') else get_QColor_rgba(fallback)
    return c


def get_QColor_rgba(rgba: str) -> QColor:
    """Parse an ``rgba(r,g,b,a)`` string into a ``QColor``.

    Args:
        rgba: Color string like "rgba(109,214,255,0.45)".

    Returns:
        QColor: The parsed color, or an invalid QColor if parsing fails.
    """
    m = _RGBA_RE.fullmatch(rgba.strip())
    if not m:
        return QColor()
    r, g, b = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    a = float(m.group(4))
    # Clamp ranges
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    a = max(0.0, min(1.0, a))
    c = QColor(r, g, b)
    c.setAlphaF(a)
    return c


def get_QColor_hex(hex_str: str) -> QColor:
    """Parse a hex string ("#RRGGBB" or "#RGB") into a ``QColor``.

    Args:
        hex_str: CSS-style hex color string.

    Returns:
        QColor: The parsed color, or an invalid QColor if parsing fails.
    """
    s = hex_str.strip()
    # QColor already supports #RRGGBB/#RGB parsing; return directly
    c = QColor(s)
    return c if c.isValid() else QColor()
