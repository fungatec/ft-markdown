"""Contratos de actualizacion en el nucleo: versiones SemVer, errores y nombres (FR-015, T016)."""

import re
from pathlib import Path

import pytest

from ft_markdown.core.errors import UserMessage
from ft_markdown.core.updates import (
    CHECKSUM_NAME_TEMPLATE,
    INSTALLER_NAME_TEMPLATE,
    UpdateError,
    UpdateErrorKind,
    parse_sha256,
    parse_version,
    update_error_message,
)

RAIZ = Path(__file__).resolve().parents[2]


def _v(texto):
    version = parse_version(texto)
    assert version is not None, texto
    return version


@pytest.mark.parametrize(
    "texto",
    ["1.0.0", "v1.0.0", "V1.0.0", " 1.2.3 ", "1.0.0-beta.1", "1.0.0+build.5", "v1.0.0-rc.1+abc"],
)
def test_acepta_semver_con_prefijo_v_y_build(texto):
    assert parse_version(texto) is not None


@pytest.mark.parametrize(
    "texto",
    [
        "",
        "v",
        "1",
        "1.0",
        "1.0.0.0",
        "01.0.0",
        "1.0.0-",
        "1.0.0-01",
        "1.0.0-be ta",
        "latest",
        "x" * 80,
    ],
)
def test_tag_ininterpretable_devuelve_none_y_nunca_lanza(texto):
    assert parse_version(texto) is None


def test_parse_version_con_tipos_raros_no_lanza():
    assert parse_version(None) is None  # type: ignore[arg-type]
    assert parse_version(1.0) is None  # type: ignore[arg-type]


def test_los_numeros_se_comparan_como_numeros():
    assert _v("1.10.0") > _v("1.9.0")
    assert _v("1.0.10") > _v("1.0.9")
    assert _v("1.0.0-beta.11") > _v("1.0.0-beta.2")


def test_el_build_se_ignora():
    assert _v("1.0.0+a") == _v("1.0.0+b") == _v("1.0.0")
    assert not _v("1.0.0+a") < _v("1.0.0+b")


def test_el_prefijo_v_no_cambia_la_version():
    assert _v("v1.2.3") == _v("1.2.3")


def test_precedencia_semver_completa():
    # Ejemplo de la especificacion SemVer 2.0.0, seccion 11.
    ordenadas = [
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-alpha.beta",
        "1.0.0-beta",
        "1.0.0-beta.2",
        "1.0.0-beta.11",
        "1.0.0-rc.1",
        "1.0.0",
        "1.0.1",
        "2.0.0",
    ]
    versiones = [_v(t) for t in ordenadas]
    assert sorted(reversed(versiones)) == versiones
    for menor, mayor in zip(versiones, versiones[1:]):
        assert menor < mayor and mayor > menor and menor != mayor


def test_preliminar_es_menor_que_la_final_y_se_detecta():
    assert _v("1.0.0-beta.2") < _v("1.0.0")
    assert _v("1.0.0-beta.2").is_prerelease
    assert not _v("1.0.0+build").is_prerelease


def test_texto_canonico_sin_prefijo_ni_build():
    assert str(_v("v1.0.0-beta.2+abc")) == "1.0.0-beta.2"
    assert str(_v("2.3.4")) == "2.3.4"


HASH = "ab" * 32


@pytest.mark.parametrize(
    "texto",
    [
        HASH,
        HASH + "\n",
        HASH.upper(),
        f"{HASH}  FT-Markdown-Setup-1.0.0.exe\n",
        f"{HASH} *FT-Markdown-Setup-1.0.0.exe",
        f"\ufeff{HASH}  FT-Markdown-Setup-1.0.0.exe\r\n",
    ],
)
def test_parse_sha256_acepta_hash_solo_o_con_nombre(texto):
    assert parse_sha256(texto, "FT-Markdown-Setup-1.0.0.exe") == HASH


@pytest.mark.parametrize(
    "texto",
    ["", "   \n", "xyz", HASH[:-1], HASH + "00", f"{HASH}  otro-archivo.exe", f"{HASH}x"],
)
def test_parse_sha256_rechaza_formatos_invalidos_o_de_otro_archivo(texto):
    assert parse_sha256(texto, "FT-Markdown-Setup-1.0.0.exe") is None


def test_nombres_de_assets_siguen_el_plan():
    assert INSTALLER_NAME_TEMPLATE.format(version="1.0.0") == "FT-Markdown-Setup-1.0.0.exe"
    assert CHECKSUM_NAME_TEMPLATE.format(version="1.0.0") == "FT-Markdown-Setup-1.0.0.exe.sha256"


def test_el_nombre_del_instalador_coincide_con_el_script_de_inno_setup():
    iss = (RAIZ / "packaging" / "installer.iss").read_text(encoding="utf-8")
    base = re.search(r"^OutputBaseFilename=(.+)$", iss, re.MULTILINE)
    assert base, "installer.iss debe definir OutputBaseFilename"
    esperado = base.group(1).strip().replace("{#AppVersion}", "{version}") + ".exe"
    assert esperado == INSTALLER_NAME_TEMPLATE


def test_cada_tipo_de_error_tiene_mensaje_en_espanol():
    for kind in UpdateErrorKind:
        mensaje = update_error_message(kind)
        assert isinstance(mensaje, UserMessage)
        assert mensaje.title and mensaje.cause and mensaje.suggestion


def test_el_limite_de_github_tiene_un_mensaje_claro():
    texto = update_error_message(UpdateErrorKind.RATE_LIMIT).text.lower()
    assert "límite" in texto and "github" in texto


def test_solo_no_connection_significa_que_el_servidor_no_respondio():
    for kind in UpdateErrorKind:
        assert UpdateError(kind).responded is (kind is not UpdateErrorKind.NO_CONNECTION)


def test_el_error_conserva_el_detalle_tecnico():
    error = UpdateError(UpdateErrorKind.SERVER, "HTTP 503")
    assert error.kind is UpdateErrorKind.SERVER and "503" in str(error)
