from pathlib import Path

import pytest

pytest.importorskip("PySide6.QtWidgets")
pytest.importorskip("pytestqt")

from ft_markdown.core.errors import ConversionError  # noqa: E402
from ft_markdown.core.models import ConversionResult  # noqa: E402
from ft_markdown.ui.main_window import MainWindow  # noqa: E402


class MotorFalso:
    """Cumple el contrato ConversionEngine sin usar MarkItDown."""

    def convert_file(self, path: Path) -> ConversionResult:
        if path.suffix == ".mal":
            raise ConversionError("formato no soportado")
        return ConversionResult(source=path, markdown="# Titulo\n\nTexto de prueba.")


def test_muestra_el_markdown_convertido(qtbot):
    ventana = MainWindow(MotorFalso())
    qtbot.addWidget(ventana)

    ventana.convert_path(Path("documento.pdf"))

    assert "Texto de prueba." in ventana._preview.toPlainText()
    assert "Listo" in ventana._status.text()


def test_muestra_el_error_de_conversion(qtbot):
    ventana = MainWindow(MotorFalso())
    qtbot.addWidget(ventana)

    ventana.convert_path(Path("archivo.mal"))

    assert ventana._preview.toPlainText() == ""
    assert "formato no soportado" in ventana._status.text()
