"""Ventana principal (version minima de la prueba de concepto, tarea T005).

Pendiente en tareas posteriores: tema de FungaTec y cadenas externas (T017), zona de soltar (T018),
cola de conversion en segundo plano (T013). Aqui la conversion es sincrona a proposito: es una
prueba para validar el empaquetado, no la interfaz final.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..__about__ import APP_NAME, __version__
from ..core.engine import ConversionEngine
from ..core.errors import ConversionError


class MainWindow(QMainWindow):
    def __init__(self, engine: ConversionEngine) -> None:
        super().__init__()
        self._engine = engine
        self.setWindowTitle(f"{APP_NAME} {__version__}")
        self.resize(900, 640)

        self._open_button = QPushButton("Elegir documento…")
        self._open_button.clicked.connect(self.choose_file)
        self._status = QLabel("Elige un documento para convertirlo a Markdown.")
        self._preview = QTextBrowser()
        self._preview.setOpenExternalLinks(False)

        layout = QVBoxLayout()
        layout.addWidget(self._open_button)
        layout.addWidget(self._status)
        layout.addWidget(self._preview, stretch=1)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def choose_file(self) -> None:
        name, _ = QFileDialog.getOpenFileName(
            self,
            "Elegir documento",
            "",
            "Documentos (*.pdf *.docx *.pptx *.xlsx *.xls *.html *.csv *.json *.epub);;"
            "Todos los archivos (*)",
        )
        if name:
            self.convert_path(Path(name))

    def convert_path(self, path: Path) -> None:
        QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            result = self._engine.convert_file(path)
        except ConversionError as exc:
            self._preview.clear()
            self._status.setText(f"No se pudo convertir «{path.name}»: {exc}")
        else:
            self._preview.setMarkdown(result.markdown)
            self._status.setText(f"Listo: {path.name} ({len(result.markdown):,} caracteres)")
        finally:
            QGuiApplication.restoreOverrideCursor()
