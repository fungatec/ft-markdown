"""Adaptador de MarkItDown: unico archivo que importa `markitdown` (Constitucion P1)."""

from __future__ import annotations

from pathlib import Path

from markitdown import MarkItDown

from ..core.errors import ConversionError
from ..core.models import ConversionResult


class MarkItDownEngine:
    """Implementa `core.engine.ConversionEngine` con MarkItDown.

    Los convertidores se registran de forma explicita y sin plugins externos (Constitucion P5):
    el descubrimiento de plugins por `entry_points` no es fiable dentro de un ejecutable.
    """

    def __init__(self) -> None:
        self._markitdown = MarkItDown(enable_plugins=False)

    def convert_file(self, path: Path) -> ConversionResult:
        try:
            result = self._markitdown.convert_local(path)
        except Exception as exc:  # MarkItDown lanza varios tipos; T010 los traduce uno por uno
            raise ConversionError(str(exc) or type(exc).__name__) from exc
        return ConversionResult(source=path, markdown=result.markdown, title=result.title)
