"""Politica de red compartida por las descargas (FR-015, FR-016, P11, T016)."""

import urllib.error
import urllib.request

import pytest

from ft_markdown.adapters import ffmpeg_provider, network_policy
from ft_markdown.adapters.network_policy import (
    AllowListRedirects,
    DisallowedRedirectError,
    is_allowed_url,
)


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/fungatec/ft-markdown/releases/download/v1/a.exe",
        "https://api.github.com/repos/fungatec/ft-markdown/releases",
        "https://release-assets.githubusercontent.com/x?sp=r",
        "https://githubusercontent.com/a",
    ],
)
def test_acepta_github_api_y_githubusercontent(url):
    assert is_allowed_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://api.github.com/x",
        "https://evilapi.github.com.evil.com/x",
        "https://notgithub.com/x",
        "https://gist.github.com/x",
        "https://user:pw@github.com/x",
        "https://example.com/x",
        "file:///etc/passwd",
    ],
)
def test_rechaza_otros_origenes(url):
    assert not is_allowed_url(url)


def test_redireccion_fuera_de_la_lista_lanza_un_error_especifico():
    peticion = urllib.request.Request("https://github.com/a")
    with pytest.raises(DisallowedRedirectError):
        AllowListRedirects().redirect_request(peticion, None, 302, "Found", {}, "https://evil.com/")
    assert issubclass(DisallowedRedirectError, urllib.error.URLError)


def test_ffmpeg_reutiliza_la_politica_compartida_sin_copiarla():
    assert ffmpeg_provider.is_allowed_url is network_policy.is_allowed_url
    assert isinstance(ffmpeg_provider.UrllibDownloader()._redirect_handler, AllowListRedirects)


def test_las_peticiones_solo_identifican_la_app():
    peticion = network_policy.new_request("https://api.github.com/x", accept="application/json")
    assert peticion.get_header("User-agent") == "FT-Markdown"
    assert peticion.get_header("Accept") == "application/json"
    assert set(peticion.headers) <= {"User-agent", "Accept", "X-github-api-version"}
