"""Punto de entrada de FT Markdown.

Este modulo es la raiz de composicion: es el unico lugar autorizado a conectar las capas entre si
(adapters con ui). Los imports pesados se hacen dentro de main() para que `--version` responda
sin cargar Qt ni MarkItDown.
"""

from __future__ import annotations

import sys

from .__about__ import APP_NAME, ORGANIZATION, __version__


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if "--version" in args:
        print(f"{APP_NAME} {__version__}")
        return 0

    from PySide6.QtWidgets import QApplication

    from .adapters.markitdown_engine import MarkItDownEngine
    from .ui.main_window import MainWindow

    app = QApplication(sys.argv[:1] + args)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORGANIZATION)
    window = MainWindow(MarkItDownEngine())
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
