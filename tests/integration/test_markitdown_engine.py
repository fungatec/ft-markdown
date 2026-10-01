import os
from pathlib import Path

import pytest

pytest.importorskip("markitdown")

from markitdown import (  # noqa: E402
    FileConversionException,
    MissingDependencyException,
    UnsupportedFormatException,
)
from markitdown._exceptions import FailedConversionAttempt  # noqa: E402
from requests.exceptions import ConnectionError as RequestsConnectionError  # noqa: E402

from ft_markdown.adapters.markitdown_engine import MarkItDownEngine, classify  # noqa: E402
from ft_markdown.core.errors import ConversionError, ErrorKind  # noqa: E402

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_convierte_un_pdf_local():
    resultado = MarkItDownEngine().convert_file(FIXTURES / "test.pdf")

    assert resultado.source == FIXTURES / "test.pdf"
    assert "Large language models" in resultado.markdown


def test_archivo_inexistente_lanza_conversion_error(tmp_path: Path):
    with pytest.raises(ConversionError):
        MarkItDownEngine().convert_file(tmp_path / "no_existe.pdf")


def test_formato_no_soportado_lanza_conversion_error(tmp_path: Path):
    binario = tmp_path / "datos.bin"
    binario.write_bytes(os.urandom(1024))

    with pytest.raises(ConversionError):
        MarkItDownEngine().convert_file(binario)


def test_archivo_inexistente_se_clasifica_como_no_encontrado(tmp_path: Path):
    with pytest.raises(ConversionError) as info:
        MarkItDownEngine().convert_file(tmp_path / "no_existe.pdf")
    assert info.value.kind is ErrorKind.FILE_NOT_FOUND
    assert info.value.source == tmp_path / "no_existe.pdf"


def test_binario_aleatorio_se_clasifica_como_formato_no_compatible(tmp_path: Path):
    binario = tmp_path / "datos.bin"
    binario.write_bytes(os.urandom(1024))
    with pytest.raises(ConversionError) as info:
        MarkItDownEngine().convert_file(binario)
    assert info.value.kind is ErrorKind.UNSUPPORTED_FORMAT


def test_pdf_danado_se_clasifica_como_ilegible(tmp_path: Path):
    falso = tmp_path / "roto.pdf"
    falso.write_bytes(b"%PDF-1.4\n" + os.urandom(256))
    with pytest.raises(ConversionError) as info:
        MarkItDownEngine().convert_file(falso)
    assert info.value.kind in {ErrorKind.CORRUPT_FILE, ErrorKind.UNSUPPORTED_FORMAT}


def test_resultado_vacio_se_informa_como_error_con_el_origen(tmp_path: Path, monkeypatch):
    class Vacio:
        markdown = "  \n"
        title = None

    motor = MarkItDownEngine()
    monkeypatch.setattr(motor._markitdown, "convert_local", lambda path: Vacio())
    with pytest.raises(ConversionError) as info:
        motor.convert_file(tmp_path / "escaneo.pdf")
    assert info.value.kind is ErrorKind.EMPTY_RESULT
    assert info.value.source == tmp_path / "escaneo.pdf"


def test_clasificacion_de_excepciones_de_markitdown():
    assert classify(UnsupportedFormatException("x")) is ErrorKind.UNSUPPORTED_FORMAT
    assert classify(MissingDependencyException("x")) is ErrorKind.MISSING_DEPENDENCY
    assert classify(RequestsConnectionError("x")) is ErrorKind.NETWORK
    assert classify(TimeoutError()) is ErrorKind.NETWORK
    assert classify(FileConversionException("x")) is ErrorKind.CORRUPT_FILE
    assert classify(RuntimeError("x")) is ErrorKind.UNKNOWN


def test_fallo_de_red_envuelto_por_markitdown_se_detecta_como_red():
    intento = FailedConversionAttempt(
        object(), (RequestsConnectionError, RequestsConnectionError("x"), None)
    )
    assert classify(FileConversionException(attempts=[intento])) is ErrorKind.NETWORK


def test_dependencia_faltante_envuelta_no_se_confunde_con_archivo_danado():
    intento = FailedConversionAttempt(
        object(), (MissingDependencyException, MissingDependencyException("x"), None)
    )
    assert classify(FileConversionException(attempts=[intento])) is ErrorKind.MISSING_DEPENDENCY
