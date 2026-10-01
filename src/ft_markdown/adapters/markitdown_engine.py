"""Adaptador de MarkItDown: unico archivo que importa la biblioteca (Constitucion P1).

Traduce las excepciones de MarkItDown a `ConversionError` con un `ErrorKind`, de modo que el
resto de la aplicacion no depende de la biblioteca.
"""

from __future__ import annotations

from pathlib import Path

from markitdown import (
    FileConversionException,
    MarkItDown,
    MissingDependencyException,
    UnsupportedFormatException,
)
from requests.exceptions import RequestException

from ..core.errors import ConversionError, ErrorKind
from ..core.models import ConversionResult

_NETWORK_ERRORS = (RequestException, ConnectionError, TimeoutError)


def classify(exc: BaseException) -> ErrorKind:
    """Clasifica una excepcion de MarkItDown (o de red) en un tipo de error del nucleo."""
    if isinstance(exc, FileNotFoundError):
        return ErrorKind.FILE_NOT_FOUND
    if isinstance(exc, _NETWORK_ERRORS):
        return ErrorKind.NETWORK
    if isinstance(exc, UnsupportedFormatException):
        return ErrorKind.UNSUPPORTED_FORMAT
    if isinstance(exc, MissingDependencyException):
        return ErrorKind.MISSING_DEPENDENCY
    if isinstance(exc, FileConversionException):
        # MarkItDown envuelve el fallo real: si fue de red, se informa como tal.
        for intento in exc.attempts or []:
            if intento.exc_info and isinstance(intento.exc_info[1], _NETWORK_ERRORS):
                return ErrorKind.NETWORK
        return ErrorKind.CORRUPT_FILE
    return ErrorKind.UNKNOWN


class MarkItDownEngine:
    def __init__(self) -> None:
        # Sin plugins: entry_points no es fiable dentro de un .exe (plan, P5).
        self._markitdown = MarkItDown(enable_plugins=False)

    def convert_file(self, path: Path) -> ConversionResult:
        try:
            result = self._markitdown.convert_local(path)
        except Exception as exc:
            raise ConversionError(
                str(exc) or type(exc).__name__, kind=classify(exc), source=path
            ) from exc
        if not result.markdown.strip():
            raise ConversionError("Resultado vacio", kind=ErrorKind.EMPTY_RESULT, source=path)
        return ConversionResult(source=path, markdown=result.markdown, title=result.title)
