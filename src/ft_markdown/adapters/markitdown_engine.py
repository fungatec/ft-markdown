"""Adaptador de MarkItDown: unico archivo que importa la biblioteca (Constitucion P1).

Traduce las excepciones de MarkItDown a `ConversionError` con un `ErrorKind`, de modo que el
resto de la aplicacion no depende de la biblioteca. Tambien aplica las preferencias de idioma
(`ConversionOptions`): MarkItDown usa ingles por defecto y la app trabaja en espanol.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from markitdown import (
    FileConversionException,
    MarkItDown,
    MissingDependencyException,
    UnsupportedFormatException,
)
from requests.exceptions import RequestException

from ..core.capabilities import find_for_path
from ..core.errors import ConversionError, ErrorKind
from ..core.models import ConversionOptions, ConversionResult
from . import audio_transcriber

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
        # MarkItDown envuelve el fallo real en `attempts`: se mira la causa verdadera.
        causas = [a.exc_info[1] for a in exc.attempts or [] if a.exc_info]
        if any(isinstance(c, _NETWORK_ERRORS) for c in causas):
            return ErrorKind.NETWORK
        if any(isinstance(c, MissingDependencyException) for c in causas):
            return ErrorKind.MISSING_DEPENDENCY
        return ErrorKind.CORRUPT_FILE
    return ErrorKind.UNKNOWN


class MarkItDownEngine:
    def __init__(
        self,
        options: ConversionOptions | None = None,
        *,
        ffmpeg_locator: Callable[[], Path | str | None] | None = None,
    ) -> None:
        self._options = options or ConversionOptions()
        # Se consulta en cada conversion: el componente puede descargarse con la app abierta.
        self._ffmpeg_locator = ffmpeg_locator
        # Sin plugins: entry_points no es fiable dentro de un .exe (plan, P5).
        self._markitdown = MarkItDown(enable_plugins=False)

    def convert_file(self, path: Path) -> ConversionResult:
        capacidad = find_for_path(path)
        if capacidad is not None and capacidad.id.startswith("audio"):
            return self._convert_audio(path)
        try:
            result = self._markitdown.convert_local(path)
        except Exception as exc:
            raise ConversionError(
                str(exc) or type(exc).__name__, kind=classify(exc), source=path
            ) from exc
        if not result.markdown.strip():
            raise ConversionError("Resultado vacio", kind=ErrorKind.EMPTY_RESULT, source=path)
        return ConversionResult(source=path, markdown=result.markdown, title=result.title)

    def convert_url(self, url: str) -> ConversionResult:
        try:
            result = self._markitdown.convert_url(
                url, youtube_transcript_languages=list(self._options.youtube_languages)
            )
        except Exception as exc:
            raise ConversionError(
                str(exc) or type(exc).__name__, kind=classify(exc), source=url
            ) from exc
        if not result.markdown.strip():
            raise ConversionError("Resultado vacio", kind=ErrorKind.EMPTY_RESULT, source=url)
        return ConversionResult(source=url, markdown=result.markdown, title=result.title)

    def _convert_audio(self, path: Path) -> ConversionResult:
        ffmpeg = self._ffmpeg_locator() if self._ffmpeg_locator else None
        texto = audio_transcriber.transcribe(
            path, self._options.audio_language, ffmpeg=str(ffmpeg) if ffmpeg else None
        )
        markdown = f"### Transcripción de audio\n\n{texto}\n"
        return ConversionResult(source=path, markdown=markdown, title=path.stem)
