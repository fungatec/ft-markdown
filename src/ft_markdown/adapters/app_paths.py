"""Ubicacion de los datos de la app, fuera de la carpeta de instalacion (P12)."""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_data_dir

from ..__about__ import APP_NAME


def data_dir() -> Path:
    """%APPDATA%\\FT Markdown en Windows. Sobrevive a actualizaciones y desinstalaciones."""
    return Path(user_data_dir(APP_NAME, appauthor=False, roaming=True))
