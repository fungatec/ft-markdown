"""UpdateService: busca versiones nuevas y descarga el instalador verificado (FR-015, P11, T016).

No conoce GitHub ni abre sockets por su cuenta: usa un `ReleaseSource`. No lanza el instalador
ni cierra la app; eso corresponde a un adaptador con puerto en `core` (T023).

Reglas de la consulta:
- Solo si `check_updates` esta activo, como maximo una cada 24 h y un intento por arranque.
- La comprobacion manual (`manual=True`, boton "Buscar ahora") ignora el ajuste, las 24 h y el
  limite por arranque.
- `last_update_check` se guarda cuando el servidor RESPONDIO (incluidos 403/429 y 5xx) y NO cuando
  no se pudo conectar.
- Las preliminares solo se consideran si la version instalada es preliminar.
"""

from __future__ import annotations

import hashlib
import shutil
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from ..core.settings import SettingsStore
from ..core.updates import (
    CHECKSUM_NAME_TEMPLATE,
    INSTALLER_NAME_TEMPLATE,
    MAX_CHECKSUM_BYTES,
    MAX_INSTALLER_BYTES,
    CancelCheck,
    ProgressCallback,
    Release,
    ReleaseInfo,
    ReleaseSource,
    UpdateError,
    UpdateErrorKind,
    UpdateStatus,
    parse_sha256,
    parse_version,
)

CHECK_INTERVAL = timedelta(hours=24)
_CHUNK = 1024 * 1024


@dataclass(frozen=True)
class UpdateCheck:
    status: UpdateStatus
    current: str
    release: ReleaseInfo | None = None
    error: UpdateError | None = None


def _no_progress(done: int, total: int | None) -> None:
    pass


def _never() -> bool:
    return False


class UpdateService:
    def __init__(
        self,
        source: ReleaseSource,
        settings_store: SettingsStore,
        current_version: str,
        *,
        updates_dir: Path,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._source = source
        self._store = settings_store
        self._current = current_version
        self._dir = updates_dir
        self._now = now
        self._attempted = False

    # --- consulta ----------------------------------------------------------------------------

    def check(self, *, manual: bool = False) -> UpdateCheck:
        ajustes = self._store.load()
        if not manual:
            if not ajustes.check_updates:
                return UpdateCheck(UpdateStatus.SKIPPED_DISABLED, self._current)
            if self._attempted:
                return UpdateCheck(UpdateStatus.SKIPPED_ALREADY_TRIED, self._current)
            if self._is_recent(ajustes.last_update_check):
                return UpdateCheck(UpdateStatus.SKIPPED_RECENT, self._current)
            self._attempted = True

        try:
            releases = self._source.list_releases()
        except UpdateError as error:
            if error.responded:
                self._record_check()
            return UpdateCheck(UpdateStatus.FAILED, self._current, error=error)
        self._record_check()
        return self._evaluate(releases)

    def _evaluate(self, releases: list[Release]) -> UpdateCheck:
        actual = parse_version(self._current)
        if actual is None:
            return self._failed(UpdateErrorKind.INVALID_VERSION, f"instalada: {self._current!r}")

        candidatas = []
        ilegibles = 0
        for release in releases:
            if release.draft:
                continue
            version = parse_version(release.tag)
            if version is None:
                ilegibles += 1
                continue
            preliminar = release.prerelease or version.is_prerelease
            if preliminar and not actual.is_prerelease:
                continue
            candidatas.append((version, release))
        if not candidatas:
            if ilegibles:
                return self._failed(UpdateErrorKind.INVALID_VERSION, "tags no interpretables")
            return UpdateCheck(UpdateStatus.UP_TO_DATE, self._current)

        version, release = max(candidatas, key=lambda par: par[0])
        if version == actual:
            return UpdateCheck(UpdateStatus.UP_TO_DATE, self._current)
        if version < actual:
            return UpdateCheck(UpdateStatus.AHEAD, self._current)

        nombres = {a.name: a for a in release.assets}
        instalador = nombres.get(INSTALLER_NAME_TEMPLATE.format(version=version.text))
        suma = nombres.get(CHECKSUM_NAME_TEMPLATE.format(version=version.text))
        if instalador is None or suma is None:
            return self._failed(UpdateErrorKind.MISSING_ASSET, release.tag)
        info = ReleaseInfo(
            tag=release.tag,
            version=version,
            prerelease=release.prerelease or version.is_prerelease,
            installer=instalador,
            checksum=suma,
        )
        return UpdateCheck(UpdateStatus.AVAILABLE, self._current, release=info)

    def _failed(self, kind: UpdateErrorKind, detail: str) -> UpdateCheck:
        return UpdateCheck(UpdateStatus.FAILED, self._current, error=UpdateError(kind, detail))

    def _is_recent(self, marca: str | None) -> bool:
        if not marca:
            return False
        try:
            anterior = datetime.fromisoformat(marca)
        except ValueError:
            return False
        if anterior.tzinfo is None:
            anterior = anterior.replace(tzinfo=UTC)
        ahora = self._now()
        # Una marca del futuro (reloj movido) no debe bloquear las consultas para siempre.
        return timedelta(0) <= ahora - anterior < CHECK_INTERVAL

    def _record_check(self) -> None:
        marca = self._now().astimezone(UTC).isoformat(timespec="seconds")
        try:
            self._store.save(replace(self._store.load(), last_update_check=marca))
        except OSError:
            pass  # no poder anotar la consulta nunca debe romper la app

    # --- descarga ----------------------------------------------------------------------------

    def purge(self) -> None:
        """Borra instaladores antiguos y descargas a medias."""
        if not self._dir.is_dir():
            return
        for entrada in self._dir.iterdir():
            if entrada.is_dir() and not entrada.is_symlink():
                shutil.rmtree(entrada, ignore_errors=True)
            else:
                entrada.unlink(missing_ok=True)

    def download(
        self,
        release: ReleaseInfo,
        *,
        progress: ProgressCallback = _no_progress,
        cancelled: CancelCheck = _never,
    ) -> Path:
        """Descarga el instalador, comprueba tamano y SHA-256 y devuelve su ruta.

        Lanza `UpdateError`. Si algo falla no queda ningun archivo a medias.
        """
        instalador = release.installer
        if instalador.size > MAX_INSTALLER_BYTES:
            raise UpdateError(UpdateErrorKind.TOO_LARGE, f"{instalador.size} bytes")
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            self.purge()
        except OSError as exc:
            raise UpdateError(UpdateErrorKind.DISK, str(exc)) from exc

        texto = self._source.fetch_text(release.checksum, MAX_CHECKSUM_BYTES)
        esperado = parse_sha256(texto, instalador.name)
        if esperado is None:
            raise UpdateError(UpdateErrorKind.BAD_RESPONSE, "suma de verificacion ilegible")

        parcial = self._dir / (instalador.name + ".part")
        final = self._dir / instalador.name
        try:
            self._source.download(
                instalador,
                parcial,
                max_bytes=instalador.size,
                progress=progress,
                cancelled=cancelled,
            )
            if cancelled():
                raise UpdateError(UpdateErrorKind.CANCELLED)
            self._verify(parcial, instalador.size, esperado)
            parcial.replace(final)
        except OSError as exc:
            parcial.unlink(missing_ok=True)
            raise UpdateError(UpdateErrorKind.DISK, str(exc)) from exc
        except UpdateError:
            parcial.unlink(missing_ok=True)
            raise
        return final

    @staticmethod
    def _verify(archivo: Path, tamano: int, esperado: str) -> None:
        if archivo.stat().st_size != tamano:
            raise UpdateError(UpdateErrorKind.SIZE_MISMATCH, f"esperado {tamano} bytes")
        digest = hashlib.sha256()
        with archivo.open("rb") as f:
            while bloque := f.read(_CHUNK):
                digest.update(bloque)
        if digest.hexdigest() != esperado:
            raise UpdateError(UpdateErrorKind.INTEGRITY, "SHA-256 inesperado")
