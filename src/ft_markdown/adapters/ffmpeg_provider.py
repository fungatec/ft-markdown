"""Fuente fijada de ffmpeg (LGPL) y descargador HTTPS (FR-016, P9, P11).

Compilacion: BtbN/FFmpeg-Builds, variante `win64-lgpl-shared`, serie n8.1. BtbN publica builds
diarios y solo conserva los ultimos 14 y el ULTIMO DE CADA MES (dos anos). Por eso se fija el tag
del ultimo build de un mes ya cerrado, no `latest` ni uno diario. Si el tag se retira, la descarga
falla con un error claro y se fija otro en una version nueva (T027 lo comprueba antes de publicar).
Verificado: `ffmpeg -version` no muestra --enable-gpl ni --enable-nonfree (solo --enable-version3).
"""

from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from ..core.components import (
    CancelCheck,
    CancelledError,
    ComponentSpec,
    DownloadError,
    ProgressCallback,
)

_TAG = "autobuild-2026-08-31-13-27"
_ARCHIVO = "ffmpeg-n8.1.2-50-g1a748fe2cd-win64-lgpl-shared-8.1.zip"

FFMPEG = ComponentSpec(
    id="ffmpeg",
    version="n8.1.2-50-g1a748fe2cd",
    url=f"https://github.com/BtbN/FFmpeg-Builds/releases/download/{_TAG}/{_ARCHIVO}",
    sha256="e9712ffbdb03ef71bbab660c75b835bfe698ef6fad0247c76d8d394a39a3db63",
    size_bytes=70_835_150,
    executable="bin/ffmpeg.exe",
    # ffprobe.exe: pydub lo necesita para leer MP3/M4A antes de convertirlos.
    include=("bin/ffmpeg.exe", "bin/ffprobe.exe", "bin/*.dll", "LICENSE.txt"),
    installed_bytes=144_124_387,
)

_EXACT_HOSTS = frozenset({"github.com", "githubusercontent.com"})
_SUFFIX = ".githubusercontent.com"
_CHUNK = 256 * 1024
_TIMEOUT = 30


def is_allowed_url(url: str) -> bool:
    """Solo HTTPS, sin credenciales en la URL, hacia github.com o githubusercontent.com."""
    partes = urlsplit(url)
    if partes.scheme != "https" or partes.username or partes.password:
        return False
    host = (partes.hostname or "").lower()
    return host in _EXACT_HOSTS or host.endswith(_SUFFIX)


class _AllowListRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_allowed_url(newurl):
            raise urllib.error.URLError(f"Redireccion a un origen no permitido: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class UrllibDownloader:
    """Descarga por HTTPS con la biblioteca estandar, cancelable y sin dejar parciales."""

    def __init__(self) -> None:
        self._redirect_handler = _AllowListRedirects()
        self._opener = urllib.request.build_opener(self._redirect_handler)

    def download(
        self, url: str, destino: Path, *, progress: ProgressCallback, cancelled: CancelCheck
    ) -> None:
        if not is_allowed_url(url):
            raise DownloadError(f"Origen no permitido: {url}")
        # Sin cookies ni datos de la persona: solo el nombre de la app.
        peticion = urllib.request.Request(url, headers={"User-Agent": "FT-Markdown"})
        try:
            with self._opener.open(peticion, timeout=_TIMEOUT) as respuesta:
                total = int(respuesta.headers.get("Content-Length") or 0) or None
                hecho = 0
                with destino.open("wb") as salida:
                    while bloque := respuesta.read(_CHUNK):
                        if cancelled():
                            raise CancelledError(url)
                        salida.write(bloque)
                        hecho += len(bloque)
                        progress(hecho, total)
        except (CancelledError, DownloadError):
            destino.unlink(missing_ok=True)
            raise
        except (OSError, ValueError) as exc:  # URLError, HTTPError, TimeoutError y disco
            destino.unlink(missing_ok=True)
            raise DownloadError(str(exc) or type(exc).__name__) from exc
