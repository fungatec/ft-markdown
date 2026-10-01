"""Catalogo de capacidades: la tabla 3 de la especificacion convertida en datos (P5, FR-008).

La interfaz consulta este catalogo para saber que habilitar segun la conexion, los componentes
descargados y las credenciales. Agregar una funcion futura (por ejemplo OCR) es registrar una
`Capability` nueva, sin tocar el resto del nucleo.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class InputKind(Enum):
    FILE = "file"
    URL = "url"


class Reason(Enum):
    """Por que una capacidad no esta habilitada (la interfaz lo explica a la persona)."""

    NOT_IN_VERSION = "not_in_version"
    OFFLINE = "offline"
    MISSING_COMPONENT = "missing_component"
    MISSING_CREDENTIALS = "missing_credentials"


@dataclass(frozen=True)
class Capability:
    id: str
    label: str
    input_kind: InputKind = InputKind.FILE
    extensions: tuple[str, ...] = ()
    requires_network: bool = False
    requires_credentials: bool = False
    component: str | None = None  # componente descargable necesario, p. ej. "ffmpeg"
    phase: int = 1  # 1 = incluida en la v1; 2 = prevista para una version posterior


@dataclass(frozen=True)
class Availability:
    enabled: bool
    reason: Reason | None = None


def _local(id_: str, label: str, *extensions: str) -> Capability:
    return Capability(id_, label, extensions=extensions)


CATALOG: tuple[Capability, ...] = (
    _local("pdf", "PDF", ".pdf"),
    _local("docx", "Word", ".docx"),
    _local("pptx", "PowerPoint", ".pptx"),
    _local("xlsx", "Excel", ".xlsx", ".xls"),
    _local("html", "HTML", ".html", ".htm"),
    _local("datos", "CSV, JSON y XML", ".csv", ".json", ".xml"),
    _local("texto", "Texto plano", ".txt", ".text"),
    _local("ipynb", "Jupyter Notebook", ".ipynb"),
    _local("epub", "EPUB", ".epub"),
    _local("outlook", "Correo de Outlook", ".msg"),
    _local("zip", "ZIP", ".zip"),
    _local("imagen", "Imagen (solo metadatos)", ".jpg", ".jpeg", ".png"),
    Capability("url", "Página web", InputKind.URL, requires_network=True),
    Capability("youtube", "Video de YouTube", InputKind.URL, requires_network=True),
    Capability("audio-wav", "Audio WAV", extensions=(".wav",), requires_network=True),
    Capability(
        "audio-comprimido",
        "Audio MP3 y M4A",
        extensions=(".mp3", ".m4a"),
        requires_network=True,
        component="ffmpeg",
    ),
    # Fase 2: se registran para que la interfaz pueda mostrarlas como "proximamente".
    Capability(
        "llm-descripcion",
        "Descripción de imágenes con IA",
        requires_network=True,
        requires_credentials=True,
        phase=2,
    ),
    Capability("ocr", "OCR de escaneos", requires_network=True, requires_credentials=True, phase=2),
    Capability(
        "azure",
        "Azure Document Intelligence",
        requires_network=True,
        requires_credentials=True,
        phase=2,
    ),
)

_BY_ID = {c.id: c for c in CATALOG}
_BY_EXTENSION = {e: c for c in CATALOG for e in c.extensions}


def get(id_: str) -> Capability:
    """Devuelve la capacidad con ese identificador (KeyError si no existe)."""
    return _BY_ID[id_]


def find_for_path(path: Path) -> Capability | None:
    """Capacidad que atiende la extension del archivo, o None si no se reconoce."""
    return _BY_EXTENSION.get(path.suffix.lower())


def availability(
    capability: Capability,
    *,
    online: bool,
    components: frozenset[str] = frozenset(),
    credentials: frozenset[str] = frozenset(),
) -> Availability:
    """Decide si la capacidad esta habilitada y, si no, por que (en orden de prioridad)."""
    if capability.phase != 1:
        return Availability(False, Reason.NOT_IN_VERSION)
    if capability.requires_network and not online:
        return Availability(False, Reason.OFFLINE)
    if capability.component is not None and capability.component not in components:
        return Availability(False, Reason.MISSING_COMPONENT)
    if capability.requires_credentials and not credentials:
        return Availability(False, Reason.MISSING_CREDENTIALS)
    return Availability(True)
