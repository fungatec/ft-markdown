import os
from pathlib import Path

import pytest

pytest.importorskip("markitdown")

from ft_markdown.adapters.markitdown_engine import MarkItDownEngine  # noqa: E402
from ft_markdown.core.errors import ConversionError  # noqa: E402

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
