"""Adaptador de GitHub Releases con respuestas simuladas; sin internet (FR-015, T016)."""

import io
import json
import urllib.error
from email.message import Message

import pytest

from ft_markdown.adapters.github_releases import GitHubReleases
from ft_markdown.adapters.network_policy import DisallowedRedirectError
from ft_markdown.core.updates import Asset, UpdateError, UpdateErrorKind

BASE = "https://github.com/fungatec/ft-markdown/releases/download"


class Respuesta(io.BytesIO):
    def __init__(self, cuerpo: bytes, headers: dict | None = None):
        super().__init__(cuerpo)
        self.headers = headers or {}


class Opener:
    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.peticiones = []

    def open(self, peticion, timeout=None):
        self.peticiones.append(peticion)
        r = self.respuestas.pop(0)
        if isinstance(r, BaseException):
            raise r
        return r


def _http(codigo, **headers):
    mensaje = Message()
    for k, v in headers.items():
        mensaje[k.replace("_", "-")] = v
    return urllib.error.HTTPError("https://api.github.com/x", codigo, "x", mensaje, None)


def _json(datos) -> Respuesta:
    return Respuesta(json.dumps(datos).encode())


def _release(tag="v1.0.0", prerelease=False, draft=False, assets=None):
    if assets is None:
        nombre = f"FT-Markdown-Setup-{tag.lstrip('v')}.exe"
        assets = [{"name": nombre, "browser_download_url": f"{BASE}/{tag}/{nombre}", "size": 100}]
    return {"tag_name": tag, "prerelease": prerelease, "draft": draft, "assets": assets}


def _fuente(*respuestas):
    opener = Opener(*respuestas)
    return GitHubReleases(opener=opener), opener


def test_lista_las_releases_con_sus_assets():
    fuente, opener = _fuente(_json([_release(), _release("v0.9.0", prerelease=True)]))
    releases = fuente.list_releases()
    assert [r.tag for r in releases] == ["v1.0.0", "v0.9.0"]
    assert releases[1].prerelease and not releases[0].prerelease
    assert releases[0].assets == (
        Asset("FT-Markdown-Setup-1.0.0.exe", f"{BASE}/v1.0.0/FT-Markdown-Setup-1.0.0.exe", 100),
    )
    peticion = opener.peticiones[0]
    assert peticion.full_url.startswith(
        "https://api.github.com/repos/fungatec/ft-markdown/releases?per_page="
    )
    assert peticion.get_header("User-agent") == "FT-Markdown"
    assert "json" in peticion.get_header("Accept")
    assert not peticion.has_header("Authorization")


def test_ignora_assets_y_entradas_malformados_o_de_origenes_no_permitidos():
    malos = [
        {"name": "a.exe", "browser_download_url": "https://evil.com/a.exe", "size": 1},
        {"name": "b.exe", "browser_download_url": f"{BASE}/b.exe", "size": "x"},
        {"name": 5, "browser_download_url": f"{BASE}/c.exe", "size": 1},
        "no es un dict",
    ]
    fuente, _ = _fuente(_json(["basura", _release(assets=malos)]))
    releases = fuente.list_releases()
    assert len(releases) == 1 and releases[0].assets == ()


@pytest.mark.parametrize("codigo", [403, 429])
def test_el_limite_de_uso_es_un_error_claro(codigo):
    fuente, _ = _fuente(_http(codigo, x_ratelimit_remaining="0"))
    with pytest.raises(UpdateError) as info:
        fuente.list_releases()
    assert info.value.kind is UpdateErrorKind.RATE_LIMIT and info.value.responded


@pytest.mark.parametrize("codigo", [404, 500, 502, 503])
def test_otros_codigos_http_son_error_del_servidor_y_si_hubo_respuesta(codigo):
    fuente, _ = _fuente(_http(codigo))
    with pytest.raises(UpdateError) as info:
        fuente.list_releases()
    assert info.value.kind is UpdateErrorKind.SERVER and info.value.responded


@pytest.mark.parametrize(
    "fallo", [urllib.error.URLError("sin dns"), TimeoutError(), ConnectionResetError()]
)
def test_sin_conexion_no_cuenta_como_respuesta(fallo):
    fuente, _ = _fuente(fallo)
    with pytest.raises(UpdateError) as info:
        fuente.list_releases()
    assert info.value.kind is UpdateErrorKind.NO_CONNECTION and not info.value.responded


@pytest.mark.parametrize("cuerpo", [b"<html>", b"{}", b'"x"', b"\xff\xfe"])
def test_json_invalido_o_de_forma_inesperada(cuerpo):
    fuente, _ = _fuente(Respuesta(cuerpo))
    with pytest.raises(UpdateError) as info:
        fuente.list_releases()
    assert info.value.kind is UpdateErrorKind.BAD_RESPONSE


def test_un_json_enorme_se_rechaza_por_cabecera_o_por_cuerpo():
    por_cabecera = Respuesta(b"[]", {"Content-Length": str(50 * 1024 * 1024)})
    por_cuerpo = Respuesta(b"[" + b" " * (2 * 1024 * 1024) + b"]")
    for respuesta in (por_cabecera, por_cuerpo):
        fuente, _ = _fuente(respuesta)
        with pytest.raises(UpdateError) as info:
            fuente.list_releases()
        assert info.value.kind is UpdateErrorKind.TOO_LARGE


def test_una_redireccion_no_permitida_es_respuesta_invalida_no_falta_de_red():
    fuente, _ = _fuente(DisallowedRedirectError("https://evil.com"))
    with pytest.raises(UpdateError) as info:
        fuente.list_releases()
    assert info.value.kind is UpdateErrorKind.BAD_RESPONSE


def _asset(nombre="a.sha256", url=f"{BASE}/v1/a.sha256", size=70):
    return Asset(nombre, url, size)


def test_fetch_text_devuelve_el_texto_y_respeta_el_tope():
    fuente, opener = _fuente(Respuesta(b"abc\n"), Respuesta(b"x" * 5000))
    assert fuente.fetch_text(_asset(), max_bytes=4096) == "abc\n"
    assert opener.peticiones[0].get_header("User-agent") == "FT-Markdown"
    with pytest.raises(UpdateError) as info:
        fuente.fetch_text(_asset(), max_bytes=4096)
    assert info.value.kind is UpdateErrorKind.TOO_LARGE


def test_fetch_text_rechaza_origen_no_permitido_sin_abrir_conexion():
    fuente, opener = _fuente()
    with pytest.raises(UpdateError) as info:
        fuente.fetch_text(_asset(url="https://evil.com/a"), max_bytes=100)
    assert info.value.kind is UpdateErrorKind.BAD_RESPONSE and not opener.peticiones


def test_download_escribe_el_archivo_y_avisa_del_progreso(tmp_path):
    fuente, _ = _fuente(Respuesta(b"x" * 1000, {"Content-Length": "1000"}))
    avances = []
    destino = tmp_path / "a.exe"
    fuente.download(
        _asset("a.exe", f"{BASE}/v1/a.exe", 1000),
        destino,
        max_bytes=1000,
        progress=lambda hecho, total: avances.append((hecho, total)),
        cancelled=lambda: False,
    )
    assert destino.read_bytes() == b"x" * 1000
    assert avances[-1] == (1000, 1000)


def test_download_supera_el_tope_y_borra_el_parcial(tmp_path):
    fuente, _ = _fuente(Respuesta(b"x" * 1000))
    destino = tmp_path / "a.exe"
    with pytest.raises(UpdateError) as info:
        fuente.download(
            _asset("a.exe", f"{BASE}/a.exe", 10),
            destino,
            max_bytes=10,
            progress=lambda *_: None,
            cancelled=lambda: False,
        )
    assert info.value.kind is UpdateErrorKind.TOO_LARGE and not destino.exists()


def test_download_cancelado_borra_el_parcial(tmp_path):
    fuente, _ = _fuente(Respuesta(b"x" * 1000))
    destino = tmp_path / "a.exe"
    with pytest.raises(UpdateError) as info:
        fuente.download(
            _asset("a.exe", f"{BASE}/a.exe", 1000),
            destino,
            max_bytes=1000,
            progress=lambda *_: None,
            cancelled=lambda: True,
        )
    assert info.value.kind is UpdateErrorKind.CANCELLED and not destino.exists()


def test_download_con_red_caida_a_medias_borra_el_parcial(tmp_path):
    class Rota(Respuesta):
        def read(self, n=-1):
            raise ConnectionResetError()

    fuente, _ = _fuente(Rota(b""))
    destino = tmp_path / "a.exe"
    with pytest.raises(UpdateError) as info:
        fuente.download(
            _asset("a.exe", f"{BASE}/a.exe", 10),
            destino,
            max_bytes=10,
            progress=lambda *_: None,
            cancelled=lambda: False,
        )
    assert info.value.kind is UpdateErrorKind.NO_CONNECTION and not destino.exists()


def test_download_con_error_de_disco_es_error_de_disco(tmp_path):
    fuente, _ = _fuente(Respuesta(b"x"))
    with pytest.raises(UpdateError) as info:
        fuente.download(
            _asset("a.exe", f"{BASE}/a.exe", 1),
            tmp_path / "no-existe" / "a.exe",
            max_bytes=1,
            progress=lambda *_: None,
            cancelled=lambda: False,
        )
    assert info.value.kind is UpdateErrorKind.DISK
