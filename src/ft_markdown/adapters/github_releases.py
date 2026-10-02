"""Origen de versiones: GitHub Releases de fungatec/ft-markdown (FR-015, P11, T016).

Una consulta publica y sin autenticacion a `GET /repos/{dueno}/ft-markdown/releases` (lista corta)
y, solo si la persona confirma, la descarga del instalador y de su `.sha256`. Usa la politica de
red compartida (`network_policy`). Todo fallo sale como `UpdateError`; nunca otra excepcion.
"""

from __future__ import annotations

import json
import urllib.error
from pathlib import Path
from typing import Any

from ..core.updates import (
    MAX_JSON_BYTES,
    Asset,
    CancelCheck,
    ProgressCallback,
    Release,
    UpdateError,
    UpdateErrorKind,
)
from .network_policy import (
    TIMEOUT,
    DisallowedRedirectError,
    build_opener,
    is_allowed_url,
    new_request,
)

REPO = "fungatec/ft-markdown"
_PER_PAGE = 10
_CHUNK = 256 * 1024
_API_VERSION = "2022-11-28"


class GitHubReleases:
    def __init__(self, repo: str = REPO, *, opener: Any = None) -> None:
        self._url = f"https://api.github.com/repos/{repo}/releases?per_page={_PER_PAGE}"
        self._opener = opener if opener is not None else build_opener()

    # --- consulta ----------------------------------------------------------------------------

    def list_releases(self) -> list[Release]:
        peticion = new_request(self._url, accept="application/vnd.github+json")
        peticion.add_header("X-GitHub-Api-Version", _API_VERSION)
        cuerpo = self._read(peticion, MAX_JSON_BYTES)
        try:
            datos = json.loads(cuerpo.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise UpdateError(UpdateErrorKind.BAD_RESPONSE, "JSON invalido") from exc
        if not isinstance(datos, list):
            raise UpdateError(UpdateErrorKind.BAD_RESPONSE, "Se esperaba una lista")
        releases = [r for r in (_release(d) for d in datos) if r is not None]
        return releases

    # --- descargas ---------------------------------------------------------------------------

    def fetch_text(self, asset: Asset, max_bytes: int) -> str:
        cuerpo = self._read(self._asset_request(asset), max_bytes)
        try:
            return cuerpo.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UpdateError(UpdateErrorKind.BAD_RESPONSE, "Texto no UTF-8") from exc

    def download(
        self,
        asset: Asset,
        destino: Path,
        *,
        max_bytes: int,
        progress: ProgressCallback,
        cancelled: CancelCheck,
    ) -> None:
        peticion = self._asset_request(asset)
        try:
            try:
                with self._opener.open(peticion, timeout=TIMEOUT) as respuesta:
                    total = _content_length(respuesta)
                    if total is not None and total > max_bytes:
                        raise UpdateError(UpdateErrorKind.TOO_LARGE, f"{total} bytes")
                    hecho = 0
                    with _open_for_write(destino) as salida:
                        while bloque := respuesta.read(_CHUNK):
                            if cancelled():
                                raise UpdateError(UpdateErrorKind.CANCELLED)
                            hecho += len(bloque)
                            if hecho > max_bytes:
                                raise UpdateError(UpdateErrorKind.TOO_LARGE, f">{max_bytes} bytes")
                            _write(salida, bloque)
                            progress(hecho, total)
            except UpdateError:
                raise
            except Exception as exc:  # noqa: BLE001 - se traduce siempre a UpdateError
                raise _translate(exc) from exc
        except UpdateError:
            destino.unlink(missing_ok=True)
            raise

    # --- internos ----------------------------------------------------------------------------

    def _asset_request(self, asset: Asset):
        if not is_allowed_url(asset.url):
            raise UpdateError(UpdateErrorKind.BAD_RESPONSE, f"Origen no permitido: {asset.url}")
        return new_request(asset.url)

    def _read(self, peticion, max_bytes: int) -> bytes:
        try:
            with self._opener.open(peticion, timeout=TIMEOUT) as respuesta:
                total = _content_length(respuesta)
                if total is not None and total > max_bytes:
                    raise UpdateError(UpdateErrorKind.TOO_LARGE, f"{total} bytes")
                cuerpo = respuesta.read(max_bytes + 1)
        except UpdateError:
            raise
        except Exception as exc:  # noqa: BLE001 - se traduce siempre a UpdateError
            raise _translate(exc) from exc
        if len(cuerpo) > max_bytes:
            raise UpdateError(UpdateErrorKind.TOO_LARGE, f">{max_bytes} bytes")
        return cuerpo


def _open_for_write(destino: Path):
    try:
        return destino.open("wb")
    except OSError as exc:
        raise UpdateError(UpdateErrorKind.DISK, str(exc)) from exc


def _write(salida, bloque: bytes) -> None:
    try:
        salida.write(bloque)
    except OSError as exc:
        raise UpdateError(UpdateErrorKind.DISK, str(exc)) from exc


def _content_length(respuesta) -> int | None:
    try:
        valor = int(respuesta.headers.get("Content-Length") or 0)
    except (ValueError, TypeError, AttributeError):
        return None
    return valor or None


def _translate(exc: Exception) -> UpdateError:
    if isinstance(exc, DisallowedRedirectError):
        return UpdateError(UpdateErrorKind.BAD_RESPONSE, str(exc))
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code in (403, 429):
            return UpdateError(UpdateErrorKind.RATE_LIMIT, f"HTTP {exc.code}")
        return UpdateError(UpdateErrorKind.SERVER, f"HTTP {exc.code}")
    if isinstance(exc, OSError):  # URLError, TimeoutError, conexion caida
        return UpdateError(UpdateErrorKind.NO_CONNECTION, str(exc) or type(exc).__name__)
    return UpdateError(UpdateErrorKind.BAD_RESPONSE, type(exc).__name__)


def _release(datos: Any) -> Release | None:
    if not isinstance(datos, dict) or not isinstance(datos.get("tag_name"), str):
        return None
    assets = []
    crudos = datos.get("assets")
    for crudo in crudos if isinstance(crudos, list) else []:
        if not isinstance(crudo, dict):
            continue
        nombre, url, tamano = (
            crudo.get("name"),
            crudo.get("browser_download_url"),
            crudo.get("size"),
        )
        if (
            isinstance(nombre, str)
            and isinstance(url, str)
            and isinstance(tamano, int)
            and not isinstance(tamano, bool)
            and tamano >= 0
            and is_allowed_url(url)
        ):
            assets.append(Asset(nombre, url, tamano))
    return Release(
        tag=datos["tag_name"],
        prerelease=datos.get("prerelease") is True,
        draft=datos.get("draft") is True,
        assets=tuple(assets),
    )
