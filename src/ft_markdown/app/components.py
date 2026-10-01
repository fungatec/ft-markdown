"""ComponentManager: obtiene componentes pesados bajo demanda y los registra (FR-016, T015).

Flujo de `ensure`: ya instalado -> devuelve la ruta; si no, pide confirmacion, comprueba el
espacio libre, descarga a una carpeta temporal, verifica el SHA-256 ANTES de abrir el zip,
extrae solo lo necesario y mueve el resultado a su sitio de golpe. Si algo falla o se cancela, no
queda nada a medias. Los componentes son regenerables: viven fuera de los datos del usuario.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import shutil
import uuid
import zipfile
from collections.abc import Callable, Iterable
from pathlib import Path, PurePosixPath

from ..core.components import (
    CancelCheck,
    CancelledError,
    ComponentSpec,
    DeclinedError,
    Downloader,
    InsufficientSpaceError,
    IntegrityError,
    ProgressCallback,
    UnsafeArchiveError,
)

MANIFEST = "manifest.json"
SPACE_MARGIN = 50 * 1024 * 1024
_CHUNK = 1024 * 1024


def _free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def _no_progress(done: int, total: int | None) -> None:
    pass


def _never() -> bool:
    return False


class ComponentManager:
    def __init__(
        self,
        root: Path,
        downloader: Downloader,
        *,
        disk_free: Callable[[Path], int] = _free_bytes,
    ) -> None:
        self._root = root
        self._downloader = downloader
        self._disk_free = disk_free

    def executable(self, spec: ComponentSpec) -> Path | None:
        """Ruta del ejecutable si ESTA version exacta esta instalada e intacta, o None."""
        carpeta = self._folder(spec)
        try:
            registro = json.loads((carpeta / MANIFEST).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(registro, dict) or any(
            registro.get(k) != v
            for k, v in (("id", spec.id), ("version", spec.version), ("sha256", spec.sha256))
        ):
            return None
        exe = carpeta / spec.executable
        return exe if exe.is_file() else None

    def installed_ids(self, specs: Iterable[ComponentSpec]) -> frozenset[str]:
        """Identificadores instalados; es lo que espera `capabilities.availability`."""
        return frozenset(s.id for s in specs if self.executable(s) is not None)

    def ensure(
        self,
        spec: ComponentSpec,
        *,
        confirm: Callable[[ComponentSpec], bool],
        progress: ProgressCallback = _no_progress,
        cancelled: CancelCheck = _never,
    ) -> Path:
        """Devuelve el ejecutable, descargandolo si hace falta y la persona lo confirma."""
        ya = self.executable(spec)
        if ya is not None:
            return ya
        if not confirm(spec):
            raise DeclinedError(spec.id)

        self._root.mkdir(parents=True, exist_ok=True)
        self._require_space(spec.size_bytes + spec.installed_bytes)
        temporal = self._root / f".descarga-{uuid.uuid4().hex}"
        temporal.mkdir()
        try:
            archivo = temporal / "descarga.zip"
            self._downloader.download(spec.url, archivo, progress=progress, cancelled=cancelled)
            if cancelled():
                raise CancelledError(spec.id)
            self._verify(archivo, spec)
            contenido = temporal / "contenido"
            self._extract(archivo, contenido, spec)
            (contenido / MANIFEST).write_text(
                json.dumps({"id": spec.id, "version": spec.version, "sha256": spec.sha256}),
                encoding="utf-8",
            )
            destino = self._folder(spec)
            if destino.exists():
                shutil.rmtree(destino)
            destino.parent.mkdir(parents=True, exist_ok=True)
            contenido.replace(destino)
            self._remove_other_versions(spec)
            return destino / spec.executable
        finally:
            shutil.rmtree(temporal, ignore_errors=True)

    def _folder(self, spec: ComponentSpec) -> Path:
        return self._root / spec.id / spec.version

    def _require_space(self, needed: int) -> None:
        if self._disk_free(self._root) < needed + SPACE_MARGIN:
            raise InsufficientSpaceError(f"Se necesitan {needed + SPACE_MARGIN} bytes libres")

    def _verify(self, archivo: Path, spec: ComponentSpec) -> None:
        digest = hashlib.sha256()
        with archivo.open("rb") as f:
            while bloque := f.read(_CHUNK):
                digest.update(bloque)
        if digest.hexdigest() != spec.sha256.lower():
            raise IntegrityError(f"SHA-256 inesperado para {spec.id} {spec.version}")

    def _extract(self, archivo: Path, destino: Path, spec: ComponentSpec) -> None:
        try:
            zf = zipfile.ZipFile(archivo)
        except zipfile.BadZipFile as exc:
            raise UnsafeArchiveError("El archivo descargado no es un zip valido") from exc
        with zf:
            elegidos: list[tuple[zipfile.ZipInfo, PurePosixPath]] = []
            for info in zf.infolist():
                partes = _safe_parts(info.filename)
                if info.is_dir() or len(partes) < 2:
                    continue
                relativa = PurePosixPath(*partes[1:])  # se quita la carpeta raiz del zip
                if any(fnmatch.fnmatchcase(str(relativa), p) for p in spec.include):
                    elegidos.append((info, relativa))
            if not any(str(rel) == spec.executable for _, rel in elegidos):
                raise UnsafeArchiveError(f"El zip no trae {spec.executable}")
            self._require_space(sum(info.file_size for info, _ in elegidos))
            for info, relativa in elegidos:
                salida = destino.joinpath(*relativa.parts)
                salida.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as origen, salida.open("wb") as fuera:
                    shutil.copyfileobj(origen, fuera)

    def _remove_other_versions(self, spec: ComponentSpec) -> None:
        for carpeta in (self._root / spec.id).iterdir():
            if carpeta.is_dir() and carpeta.name != spec.version:
                shutil.rmtree(carpeta, ignore_errors=True)


def _safe_parts(nombre: str) -> tuple[str, ...]:
    """Partes de la ruta de una entrada del zip; rechaza absolutas, con unidad o con `..`."""
    normal = nombre.replace("\\", "/")
    partes = tuple(p for p in normal.split("/") if p not in ("", "."))
    if normal.startswith("/") or ".." in partes or any(":" in p for p in partes):
        raise UnsafeArchiveError(f"Ruta peligrosa dentro del zip: {nombre!r}")
    return partes
