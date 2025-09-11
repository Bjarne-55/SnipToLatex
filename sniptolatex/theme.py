from __future__ import annotations

from pathlib import Path
from typing import Dict, Mapping


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
    """Load a QSS stylesheet by name from sniptolatex/styles and resolve tokens.

    - name: filename without extension (e.g., "settings_dialog").
    - colors: optional mapping overriding DEFAULT_COLORS.
    """
    path = _styles_dir() / f"{name}.qss"
    raw = path.read_text(encoding="utf-8")
    return resolve_qss(raw, colors)


def resolve_qss(qss: str, colors: Mapping[str, str] | None = None) -> str:
    palette = dict(DEFAULT_COLORS)
    if colors:
        palette.update(colors)
    # Replace each token. Order doesn't matter as tokens are distinct.
    for token, value in palette.items():
        qss = qss.replace(token, value)
    return qss
