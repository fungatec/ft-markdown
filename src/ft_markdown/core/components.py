"""Contratos de los componentes descargables bajo demanda (FR-016, T015).

Un componente es un programa opcional y pesado (hoy solo ffmpeg) que no viaja en el instalador.
`ComponentSpec` lo describe de forma inmutable, con la version y el SHA-256 exactos que se
aceptan; `Downloader` es el puerto por el que se baja, para poder sustituirlo en las pruebas.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

# progreso(bytes_descargados, bytes_totales o None si se desconoce)
ProgressCallback = Callable[[int, int | None], None]
CancelCheck = Callable[[], bool]


@dataclass(frozen=True)
class ComponentSpec:
    id: str
    version: str
    url: str
    sha256: str  # del archivo descargado completo, en minusculas
    size_bytes: int  # tamano de la descarga, para avisar y comprobar el espacio libre
    executable: str  # ruta relativa del ejecutable dentro de la carpeta instalada
    include: tuple[str, ...]  # patrones (fnmatch) de lo que se extrae; el resto se ignora
    installed_bytes: int = 0  # estimado, ya extraido


class Downloader(Protocol):
    def download(
        self, url: str, destino: Path, *, progress: ProgressCallback, cancelled: CancelCheck
    ) -> None:
        """Escribe el contenido de `url` en `destino`. Lanza CancelledError o DownloadError."""
        ...


class ComponentError(Exception):
    """Base de los fallos al obtener un componente."""


class DeclinedError(ComponentError):
    """La persona no confirmo la descarga."""


class CancelledError(ComponentError):
    """La descarga se cancelo."""


class DownloadError(ComponentError):
    """No se pudo descargar (red caida, origen no permitido, respuesta invalida)."""


class IntegrityError(ComponentError):
    """El archivo descargado no coincide con el SHA-256 fijado."""


class InsufficientSpaceError(ComponentError):
    """No hay espacio libre suficiente para descargar e instalar."""


class UnsafeArchiveError(ComponentError):
    """El zip contiene rutas peligrosas o no trae el ejecutable esperado."""
