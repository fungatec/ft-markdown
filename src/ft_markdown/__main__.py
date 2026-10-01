"""Punto de entrada de FT Markdown.

Este modulo es la raiz de composicion: es el unico lugar autorizado a conectar las capas entre si
(adapters con ui). Los imports pesados se hacen dentro de main() para que `--version` responda
sin cargar Qt ni MarkItDown.
"""

from __future__ import annotations

import sys

from .__about__ import APP_NAME, ORGANIZATION, __version__


def _selftest(salida: str) -> int:
    """Convierte un HTML temporal con el motor real y escribe el resultado en `salida`.

    Existe para verificar el .exe empaquetado (scripts/build.ps1): una app de ventana no tiene
    consola, asi que el resultado se deja en un archivo. Ejercita MarkItDown y Magika (modelo
    ONNX), que es justo lo que puede romperse al empaquetar.
    """
    import tempfile
    from pathlib import Path

    try:
        from .adapters.markitdown_engine import MarkItDownEngine

        with tempfile.TemporaryDirectory() as tmp:
            muestra = Path(tmp) / "muestra.html"
            muestra.write_text("<h1>Hola FungaTec</h1><p>Prueba</p>", encoding="utf-8")
            markdown = MarkItDownEngine().convert_file(muestra).markdown
        if "Hola FungaTec" not in markdown:
            raise RuntimeError(f"Salida inesperada: {markdown!r}")
        informe = f"OK {APP_NAME} {__version__}: {markdown.strip()}"
        Path(salida).write_text(informe, encoding="utf-8")
        return 0
    except Exception as exc:  # noqa: BLE001 - se informa cualquier fallo en el archivo
        Path(salida).write_text(f"ERROR {type(exc).__name__}: {exc}", encoding="utf-8")
        return 1


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if "--version" in args:
        print(f"{APP_NAME} {__version__}")
        return 0
    if "--selftest" in args:
        indice = args.index("--selftest") + 1
        if indice >= len(args):
            return 2
        return _selftest(args[indice])

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
