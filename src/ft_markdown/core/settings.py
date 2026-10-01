"""Ajustes de la persona usuaria (FR-006, FR-012) y contrato de su almacenamiento."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

THEMES = ("dark", "light", "system")


@dataclass(frozen=True)
class Settings:
    output_dir: str | None = None  # ultima carpeta de salida usada (FR-006)
    theme: str = "dark"  # oscuro por defecto (P6)
    check_updates: bool = True  # FR-015: se puede desactivar
    audio_language: str = "es-MX"  # FR-010
    last_update_check: str | None = None  # ISO 8601; limita la consulta a una por dia (P11)


class SettingsStore(Protocol):
    def load(self) -> Settings: ...

    def save(self, settings: Settings) -> None: ...
