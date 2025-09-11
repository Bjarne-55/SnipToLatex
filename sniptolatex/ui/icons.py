"""Shared icon loading helpers for the UI (PyQt6).

These helpers centralize how we resolve asset paths and load SVG/bitmap icons
as ``QIcon``/``QPixmap`` with optional scaling. They are intentionally tiny and
have no side effects beyond returning loaded objects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap


def icon_path(name: str) -> Path:
    """Return the absolute path to an icon asset under ``ui/assets/icons``.

    Args:
        name: File name, e.g., ``"eye.svg"``.

    Returns:
        Path: Resolved absolute file path (not validated).
    """
    return Path(__file__).parent / "assets" / "icons" / name


def load_icon(name: str) -> QIcon:
    """Load an icon by file name.

    Args:
        name: File name under ``ui/assets/icons``.

    Returns:
        QIcon: The loaded icon, or an empty ``QIcon`` if loading fails.
    """
    try:
        p = icon_path(name)
        return QIcon(str(p))
    except Exception:
        return QIcon()


def load_pixmap(name: str, size: Optional[QSize] = None) -> QPixmap:
    """Load an icon as a pixmap, optionally scaled.

    Args:
        name: File name under ``ui/assets/icons``.
        size: Optional target size. If provided, the pixmap is scaled to fit
            while preserving aspect ratio with smooth transformation.

    Returns:
        QPixmap: Loaded (and optionally scaled) pixmap; may be null if failed.
    """
    try:
        pm = QPixmap(str(icon_path(name)))
        if size is not None and not pm.isNull():
            pm = pm.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        return pm
    except Exception:
        return QPixmap()

