"""Descarga de ffmpeg: fuente fijada y politica de redirecciones (FR-016, P11)."""

import re
import urllib.error
import urllib.request

import pytest

from ft_markdown.adapters.ffmpeg_provider import FFMPEG, UrllibDownloader, is_allowed_url


def test_la_fuente_fijada_es_un_tag_fechado_de_fin_de_mes_y_https():
    assert FFMPEG.id == "ffmpeg"
    assert FFMPEG.url.startswith("https://github.com/BtbN/FFmpeg-Builds/releases/download/")
    assert "/download/latest/" not in FFMPEG.url
    assert re.search(r"/autobuild-\d{4}-\d{2}-(28|29|30|31)-\d{2}-\d{2}/", FFMPEG.url)
    assert "win64-lgpl-shared" in FFMPEG.url
    assert re.fullmatch(r"[0-9a-f]{64}", FFMPEG.sha256)
    assert FFMPEG.executable == "bin/ffmpeg.exe" and "bin/*.dll" in FFMPEG.include


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/x/y.zip",
        "https://release-assets.githubusercontent.com/github-production-release-asset/1/2?sp=r",
        "https://objects.githubusercontent.com/a",
        "https://githubusercontent.com/a",
    ],
)
def test_acepta_github_y_githubusercontent_con_subdominios(url):
    assert is_allowed_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/a.zip",
        "https://evilgithubusercontent.com/a",
        "https://githubusercontent.com.evil.com/a",
        "https://github.com.evil.com/a",
        "https://user@evil.com/a",
        "ftp://github.com/a",
        "https://example.com/a",
    ],
)
def test_rechaza_http_y_otros_dominios(url):
    assert not is_allowed_url(url)


def test_una_redireccion_fuera_de_la_lista_se_rechaza():
    gestor = UrllibDownloader()._redirect_handler
    peticion = urllib.request.Request("https://github.com/a.zip")
    with pytest.raises(urllib.error.URLError):
        gestor.redirect_request(peticion, None, 302, "Found", {}, "https://evil.example.com/a.zip")
    with pytest.raises(urllib.error.URLError):
        gestor.redirect_request(peticion, None, 302, "Found", {}, "http://github.com/a.zip")
    siguiente = gestor.redirect_request(
        peticion, None, 302, "Found", {}, "https://release-assets.githubusercontent.com/x"
    )
    assert siguiente is not None
