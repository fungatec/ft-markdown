"""Politica de red compartida por las descargas: ffmpeg (FR-016) y actualizaciones (FR-015).

Una sola regla (P11): solo HTTPS, sin credenciales en la URL, hacia GitHub y su CDN, y con la
misma lista blanca tambien en cada redireccion. Las peticiones solo se identifican con el nombre
de la app: sin cookies, sin token y sin datos de la persona.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from urllib.parse import urlsplit

USER_AGENT = "FT-Markdown"
TIMEOUT = 30

# github.com (releases), api.github.com (consulta de versiones) y *.githubusercontent.com (CDN).
_EXACT_HOSTS = frozenset({"github.com", "api.github.com", "githubusercontent.com"})
_SUFFIX = ".githubusercontent.com"


def is_allowed_url(url: str) -> bool:
    """Solo HTTPS, sin credenciales en la URL, hacia los origenes de GitHub permitidos."""
    partes = urlsplit(url)
    if partes.scheme != "https" or partes.username or partes.password:
        return False
    host = (partes.hostname or "").lower()
    return host in _EXACT_HOSTS or host.endswith(_SUFFIX)


class DisallowedRedirectError(urllib.error.URLError):
    """Una redireccion apunta fuera de la lista blanca."""


class AllowListRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_allowed_url(newurl):
            raise DisallowedRedirectError(f"Redireccion a un origen no permitido: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def build_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(AllowListRedirects())


def new_request(url: str, *, accept: str | None = None) -> urllib.request.Request:
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    return urllib.request.Request(url, headers=headers)
