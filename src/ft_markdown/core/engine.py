"""Contrato del motor de conversion (Constitucion P1).

Las capas superiores dependen de este contrato, nunca de una biblioteca concreta.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .models import ConversionResult


class ConversionEngine(Protocol):
    """Convierte documentos a Markdown."""

    def convert_file(self, path: Path) -> ConversionResult:
        """Convierte un archivo local. Lanza ConversionError si no es posible."""
        ...
