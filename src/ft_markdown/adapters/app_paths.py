"""Ubicacion de los datos de la app, fuera de la carpeta de instalacion (P12)."""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_data_dir

from ..__about__ import APP_NAME


def data_dir() -> Path:
    """%APPDATA%\\FT Markdown en Windows. Sobrevive a actualizaciones y desinstalaciones."""
    return Path(user_data_dir(APP_NAME, appauthor=False, roaming=True))


def local_data_dir() -> Path:
    """%LOCALAPPDATA%\\FT Markdown: datos regenerables que no deben sincronizarse entre equipos."""
    return Path(user_data_dir(APP_NAME, appauthor=False, roaming=False))


def components_dir() -> Path:
    """Donde se instalan los componentes descargados (ffmpeg); se pueden volver a bajar."""
    return local_data_dir() / "components"


def updates_dir() -> Path:
    """Donde se guarda el instalador descargado; se vacia en cada descarga nueva."""
    return local_data_dir() / "updates"
