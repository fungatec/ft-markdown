"""Contratos de actualizacion (FR-015, P11, T016): versiones SemVer, errores y puertos.

El nucleo no conoce GitHub: el adaptador entrega `Release` ya normalizadas y el servicio de la
capa `app` decide. Aqui viven el comparador de versiones (SemVer 2.0.0 completo, sin dependencias),
los tipos de fallo con su mensaje en espanol y los contratos de la fuente de versiones.

Limitacion conocida: el SHA-256 que acompana al instalador prueba INTEGRIDAD (la descarga no se
corrompio ni se trunco), no AUTENTICIDAD: quien controle la release puede cambiar instalador y hash
a la vez. La autenticidad llegara con la firma de codigo (plan §6).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol

from .errors import UserMessage

# Nombres de los assets de cada release; deben coincidir con OutputBaseFilename de
# packaging/installer.iss (lo vigila tests/unit/test_updates_core.py).
INSTALLER_NAME_TEMPLATE = "FT-Markdown-Setup-{version}.exe"
CHECKSUM_NAME_TEMPLATE = INSTALLER_NAME_TEMPLATE + ".sha256"

# Topes de tamano: lo que se lee de la red nunca supera esto.
MAX_JSON_BYTES = 1024 * 1024
MAX_CHECKSUM_BYTES = 4096
MAX_INSTALLER_BYTES = 300 * 1024 * 1024

ProgressCallback = Callable[[int, int | None], None]
CancelCheck = Callable[[], bool]

# --- versiones -------------------------------------------------------------------------------

_NUM = r"(?:0|[1-9]\d*)"
_PRE_ID = r"(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
_VERSION_RE = re.compile(
    rf"^[vV]?({_NUM})\.({_NUM})\.({_NUM})"
    rf"(?:-({_PRE_ID}(?:\.{_PRE_ID})*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
_MAX_VERSION_CHARS = 64


@dataclass(frozen=True)
class Version:
    """Version SemVer 2.0.0. El `+build` se descarta: no influye en la precedencia."""

    major: int
    minor: int
    patch: int
    pre: tuple[int | str, ...] = ()

    @property
    def is_prerelease(self) -> bool:
        return bool(self.pre)

    @property
    def text(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        return base + ("-" + ".".join(str(p) for p in self.pre) if self.pre else "")

    def __str__(self) -> str:
        return self.text

    def _key(self) -> tuple:
        # Una version final es mayor que cualquier preliminar de la misma terna; entre
        # identificadores, los numericos van antes que los alfanumericos.
        pre = tuple((0, p, "") if isinstance(p, int) else (1, 0, p) for p in self.pre)
        return (self.major, self.minor, self.patch, not self.pre, pre)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._key() < other._key()

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._key() > other._key()

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._key() <= other._key()

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._key() >= other._key()


def parse_version(text: str) -> Version | None:
    """Interpreta `1.2.3`, `v1.2.3-beta.1+build`. Devuelve None si no es SemVer; nunca lanza."""
    if not isinstance(text, str):
        return None
    texto = text.strip()
    if not texto or len(texto) > _MAX_VERSION_CHARS:
        return None
    m = _VERSION_RE.match(texto)
    if m is None:
        return None
    pre = tuple(int(p) if p.isdigit() else p for p in m.group(4).split(".")) if m.group(4) else ()
    return Version(int(m.group(1)), int(m.group(2)), int(m.group(3)), pre)


# --- suma de verificacion --------------------------------------------------------------------

_SHA_RE = re.compile(r"^([0-9A-Fa-f]{64})(?:[ \t]+\*?(.+?))?[ \t]*$")


def parse_sha256(text: str, filename: str) -> str | None:
    """Extrae el hash (en minusculas) de un `.sha256`: `<hash>` o `<hash>  <archivo>`.

    Si el archivo trae un nombre, debe ser el del instalador esperado; si no, se rechaza.
    """
    for linea in text.lstrip("﻿").splitlines():
        linea = linea.strip()
        if not linea:
            continue
        m = _SHA_RE.match(linea)
        if m is None or (m.group(2) is not None and m.group(2) != filename):
            return None
        return m.group(1).lower()
    return None


# --- modelos ---------------------------------------------------------------------------------


@dataclass(frozen=True)
class Asset:
    name: str
    url: str
    size: int


@dataclass(frozen=True)
class Release:
    """Una release tal como la publica el origen, sin interpretar."""

    tag: str
    prerelease: bool
    draft: bool
    assets: tuple[Asset, ...]


@dataclass(frozen=True)
class ReleaseInfo:
    """Una version nueva lista para descargarse."""

    tag: str
    version: Version
    prerelease: bool
    installer: Asset
    checksum: Asset


class UpdateStatus(Enum):
    AVAILABLE = "available"  # hay una version mas nueva
    UP_TO_DATE = "up_to_date"  # la instalada es la ultima publicada (o no hay nada publicado)
    AHEAD = "ahead"  # la publicada es mas antigua que la instalada
    FAILED = "failed"
    SKIPPED_DISABLED = "skipped_disabled"  # desactivado en ajustes
    SKIPPED_RECENT = "skipped_recent"  # ya se consulto hace menos de 24 h
    SKIPPED_ALREADY_TRIED = "skipped_already_tried"  # ya se intento en este arranque


# --- errores ---------------------------------------------------------------------------------


class UpdateErrorKind(Enum):
    NO_CONNECTION = "no_connection"
    RATE_LIMIT = "rate_limit"
    SERVER = "server"
    BAD_RESPONSE = "bad_response"
    TOO_LARGE = "too_large"
    INVALID_VERSION = "invalid_version"
    MISSING_ASSET = "missing_asset"
    SIZE_MISMATCH = "size_mismatch"
    INTEGRITY = "integrity"
    DISK = "disk"
    CANCELLED = "cancelled"


class UpdateError(Exception):
    """Fallo al buscar o descargar una actualizacion. Nunca se filtra otra excepcion."""

    def __init__(self, kind: UpdateErrorKind, detail: str = "") -> None:
        super().__init__(detail or kind.value)
        self.kind = kind
        self.detail = detail

    @property
    def responded(self) -> bool:
        """True si el servidor llego a contestar (aunque fuera un error)."""
        return self.kind is not UpdateErrorKind.NO_CONNECTION


_MESSAGES: dict[UpdateErrorKind, tuple[str, str, str]] = {
    UpdateErrorKind.NO_CONNECTION: (
        "No se pudo buscar actualizaciones",
        "No hay conexión con GitHub.",
        "Revisa tu conexión a internet; la app sigue funcionando con normalidad.",
    ),
    UpdateErrorKind.RATE_LIMIT: (
        "GitHub limitó las consultas",
        "Se alcanzó el límite de consultas que GitHub permite desde tu conexión.",
        "Inténtalo de nuevo en una hora.",
    ),
    UpdateErrorKind.SERVER: (
        "No se pudo buscar actualizaciones",
        "GitHub respondió con un error.",
        "Inténtalo de nuevo más tarde.",
    ),
    UpdateErrorKind.BAD_RESPONSE: (
        "No se pudo buscar actualizaciones",
        "La respuesta recibida no tiene el formato esperado.",
        "Inténtalo de nuevo más tarde.",
    ),
    UpdateErrorKind.TOO_LARGE: (
        "Descarga rechazada",
        "El archivo es más grande de lo permitido.",
        "No se instaló nada. Inténtalo de nuevo más tarde.",
    ),
    UpdateErrorKind.INVALID_VERSION: (
        "No se reconoció la versión",
        "El número de versión publicado no tiene un formato válido.",
        "Inténtalo de nuevo más tarde.",
    ),
    UpdateErrorKind.MISSING_ASSET: (
        "La actualización no está completa",
        "La versión nueva no incluye el instalador o su suma de verificación.",
        "Inténtalo de nuevo más tarde.",
    ),
    UpdateErrorKind.SIZE_MISMATCH: (
        "La descarga no coincide",
        "El tamaño del archivo descargado no es el anunciado.",
        "No se instaló nada. Inténtalo de nuevo.",
    ),
    UpdateErrorKind.INTEGRITY: (
        "La descarga no es válida",
        "El archivo descargado no coincide con su suma de verificación (SHA-256).",
        "No se instaló nada. Inténtalo de nuevo.",
    ),
    UpdateErrorKind.DISK: (
        "No se pudo guardar la actualización",
        "No fue posible escribir en la carpeta de descargas de la app.",
        "Libera espacio o revisa los permisos e inténtalo de nuevo.",
    ),
    UpdateErrorKind.CANCELLED: (
        "Descarga cancelada",
        "Cancelaste la descarga de la actualización.",
        "Puedes volver a buscarla cuando quieras.",
    ),
}


def update_error_message(kind: UpdateErrorKind) -> UserMessage:
    titulo, causa, sugerencia = _MESSAGES[kind]
    return UserMessage(title=titulo, cause=causa, suggestion=sugerencia)


# --- puerto ----------------------------------------------------------------------------------


class ReleaseSource(Protocol):
    """Origen de versiones. Todos sus fallos son `UpdateError`."""

    def list_releases(self) -> list[Release]: ...

    def fetch_text(self, asset: Asset, max_bytes: int) -> str: ...

    def download(
        self,
        asset: Asset,
        destino: Path,
        *,
        max_bytes: int,
        progress: ProgressCallback,
        cancelled: CancelCheck,
    ) -> None: ...
