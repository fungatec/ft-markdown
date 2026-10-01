"""Errores del nucleo y su traduccion a mensajes comprensibles en espanol (FR-007, HU-4).

El nucleo no conoce MarkItDown: el adaptador clasifica cada excepcion tecnica en un `ErrorKind`
y el `ErrorTranslator` convierte ese tipo en un mensaje con causa y sugerencia.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ErrorKind(Enum):
    """Categorias de fallo que la interfaz sabe explicar."""

    FILE_NOT_FOUND = "file_not_found"
    UNSUPPORTED_FORMAT = "unsupported_format"
    CORRUPT_FILE = "corrupt_file"
    MISSING_DEPENDENCY = "missing_dependency"
    MISSING_COMPONENT = "missing_component"
    NETWORK = "network"
    EMPTY_RESULT = "empty_result"
    UNKNOWN = "unknown"


class ConversionError(Exception):
    """No se pudo convertir un documento.

    `kind` dice de que tipo de fallo se trata, `source` (si se conoce) cual fue el archivo y el
    mensaje conserva el detalle tecnico original, util para "ver detalles" o para reportar.
    """

    def __init__(
        self,
        message: str = "",
        *,
        kind: ErrorKind = ErrorKind.UNKNOWN,
        source: Path | str | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.source = source


@dataclass(frozen=True)
class UserMessage:
    """Mensaje para la persona usuaria: que paso, por que y que puede hacer."""

    title: str
    cause: str
    suggestion: str
    detail: str = ""

    @property
    def text(self) -> str:
        return f"{self.title}. {self.cause} {self.suggestion}"


_IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png"})
_AUDIO_SUFFIXES = frozenset({".wav", ".mp3", ".m4a"})

_MESSAGES: dict[ErrorKind, tuple[str, str, str]] = {
    ErrorKind.FILE_NOT_FOUND: (
        "Archivo no encontrado",
        "El archivo ya no está en la ubicación indicada; pudo moverse, renombrarse o borrarse.",
        "Comprueba que el archivo siga ahí y vuelve a agregarlo.",
    ),
    ErrorKind.UNSUPPORTED_FORMAT: (
        "Formato no compatible",
        "FT Markdown no reconoce este tipo de archivo.",
        "Prueba con PDF, Word, PowerPoint, Excel, HTML, CSV, EPUB, ZIP u otro formato de la lista.",
    ),
    ErrorKind.CORRUPT_FILE: (
        "No se pudo leer el archivo",
        "El archivo parece dañado, está incompleto o está protegido con contraseña.",
        "Ábrelo con su programa original; si se ve bien, guárdalo de nuevo y reintenta.",
    ),
    ErrorKind.MISSING_DEPENDENCY: (
        "Falta un componente",
        "Esta conversión necesita una pieza que no se instaló correctamente.",
        "Reinstala FT Markdown; si el problema continúa, repórtalo con el detalle técnico.",
    ),
    ErrorKind.MISSING_COMPONENT: (
        "Falta un componente opcional",
        "Convertir audio MP3 o M4A necesita ffmpeg, que se descarga solo cuando hace falta.",
        "Acepta la descarga del componente cuando FT Markdown te la ofrezca y vuelve a intentarlo.",
    ),
    ErrorKind.NETWORK: (
        "Sin conexión a internet",
        "Esta acción necesita internet y no se pudo establecer la conexión.",
        "Revisa tu conexión e inténtalo de nuevo. Los archivos locales se convierten sin conexión.",
    ),
    ErrorKind.EMPTY_RESULT: (
        "Documento sin contenido",
        "La conversión terminó, pero no se encontró texto que mostrar.",
        "Comprueba que el documento no esté vacío.",
    ),
    ErrorKind.UNKNOWN: (
        "Error inesperado",
        "Ocurrió un problema que FT Markdown no pudo clasificar.",
        "Intenta de nuevo; si se repite, repórtalo con el detalle técnico.",
    ),
}

_PDF_WITHOUT_TEXT = (
    "PDF sin texto",
    "Probablemente es un escaneo: sus páginas son imágenes y no contienen texto seleccionable.",
    "El OCR llegará en una versión futura. Mientras tanto, aplica OCR con otra herramienta y "
    "vuelve a convertirlo.",
)

_IMAGE_WITHOUT_TEXT = (
    "Imagen sin texto extraíble",
    "Sin servicios adicionales, FT Markdown solo lee los metadatos de una imagen, no su contenido.",
    "La descripción y el reconocimiento de texto de imágenes llegarán en una versión futura.",
)

_AUDIO_WITHOUT_SPEECH = (
    "Audio sin voz reconocible",
    "El servicio de transcripción no detectó palabras en la grabación.",
    "Comprueba que la grabación tenga voz clara y que el idioma elegido sea el correcto.",
)


class ErrorTranslator:
    """Convierte excepciones tecnicas en mensajes en espanol (sin estado)."""

    def translate(self, error: BaseException) -> UserMessage:
        detail = str(error)
        if not isinstance(error, ConversionError):
            title, cause, suggestion = _MESSAGES[ErrorKind.UNKNOWN]
            return UserMessage(title, cause, suggestion, detail)

        title, cause, suggestion = self._select(error)
        return UserMessage(title, cause, suggestion, detail)

    @staticmethod
    def _select(error: ConversionError) -> tuple[str, str, str]:
        if error.kind is ErrorKind.EMPTY_RESULT and isinstance(error.source, Path):
            suffix = error.source.suffix.lower()
            if suffix == ".pdf":
                return _PDF_WITHOUT_TEXT
            if suffix in _IMAGE_SUFFIXES:
                return _IMAGE_WITHOUT_TEXT
            if suffix in _AUDIO_SUFFIXES:
                return _AUDIO_WITHOUT_SPEECH
        return _MESSAGES[error.kind]
