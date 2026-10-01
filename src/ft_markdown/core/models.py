"""Modelos de datos del nucleo. Python puro, sin dependencias externas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConversionResult:
    """Resultado de convertir un documento a Markdown."""

    source: Path
    markdown: str
    title: str | None = None
