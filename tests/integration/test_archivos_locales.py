"""T011: los archivos locales se convierten sin red (FR-002, P1).

Todos los archivos de tests/fixtures/markitdown se convierten con los sockets bloqueados: si el
motor intentara abrir una conexion, la prueba fallaria.
"""

import shutil
import socket
from pathlib import Path

import pytest

pytest.importorskip("markitdown")

from ft_markdown.adapters.markitdown_engine import MarkItDownEngine  # noqa: E402
from ft_markdown.core.errors import ConversionError, ErrorKind  # noqa: E402

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
ARCHIVOS = sorted((FIXTURES / "markitdown").glob("*.*")) + [FIXTURES / "test.pdf"]
ARCHIVOS = [a for a in ARCHIVOS if a.suffix != ".md"]

# Sin servicios extra, una imagen solo aporta metadatos y solo si exiftool esta instalado.
IMAGENES = {"test.jpg", "test_llm.jpg"}
ESCANEADOS = {"MEDRPT-2024-PAT-3847_medical_report_scan.pdf"}


@pytest.fixture
def sin_red(monkeypatch):
    intentos: list[object] = []

    def bloqueado(*args, **kwargs):
        intentos.append(args)
        raise AssertionError("El motor intento usar la red al convertir un archivo local")

    monkeypatch.setattr(socket.socket, "connect", bloqueado)
    monkeypatch.setattr(socket, "getaddrinfo", bloqueado)
    return intentos


def test_hay_al_menos_25_archivos_de_prueba():
    assert len(ARCHIVOS) >= 25


@pytest.mark.parametrize("archivo", ARCHIVOS, ids=lambda a: a.name)
def test_archivo_local_se_convierte_sin_usar_la_red(archivo: Path, sin_red):
    motor = MarkItDownEngine()
    sin_texto = archivo.name in ESCANEADOS or (
        archivo.name in IMAGENES and shutil.which("exiftool") is None
    )
    if sin_texto:
        with pytest.raises(ConversionError) as info:
            motor.convert_file(archivo)
        assert info.value.kind is ErrorKind.EMPTY_RESULT
    else:
        assert motor.convert_file(archivo).markdown.strip()
    assert sin_red == []
