"""Vigila automaticamente las reglas de arquitectura (Constitucion P1 y P2, plan seccion 2).

Reglas de dependencias entre capas internas:
    core      -> (nada)
    adapters  -> core
    app       -> core
    ui        -> core, app
La raiz de composicion (__main__.py y archivos sueltos en la raiz del paquete) puede conectar las
capas entre si, pero tampoco puede importar MarkItDown.

Reglas sobre bibliotecas externas:
    - markitdown solo se importa en adapters/markitdown_engine.py.
    - PySide6 esta prohibido en core y adapters; app solo puede usar PySide6.QtCore (senales).
"""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE = "ft_markdown"
SRC = Path(__file__).resolve().parents[2] / "src" / PACKAGE

ALLOWED_INTERNAL: dict[str, set[str]] = {
    "core": set(),
    "adapters": {"core"},
    "app": {"core"},
    "ui": {"core", "app"},
}
MARKITDOWN_OWNER = "adapters/markitdown_engine.py"


def _imported_modules(path: Path, package_parts: list[str]) -> list[list[str]]:
    """Devuelve los modulos importados por un archivo, como listas de partes absolutas."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[list[str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name.split(".") for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                found.append((node.module or "").split("."))
                continue
            base = package_parts[: len(package_parts) - (node.level - 1)]
            if node.module:
                found.append(base + node.module.split("."))
            else:  # "from . import x": cada nombre puede ser un submodulo
                found.extend(base + [alias.name] for alias in node.names)
    return found


def find_violations(root: Path) -> list[str]:
    """Busca imports que rompan las reglas. Devuelve una lista de descripciones legibles."""
    violations: list[str] = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        rel_posix = rel.as_posix()
        layer = rel.parts[0] if len(rel.parts) > 1 and rel.parts[0] in ALLOWED_INTERNAL else None
        package_parts = [PACKAGE, *rel.parts[:-1]]

        for parts in _imported_modules(path, package_parts):
            top = parts[0]

            if top == "markitdown" and rel_posix != MARKITDOWN_OWNER:
                violations.append(f"{rel_posix}: importa markitdown (solo {MARKITDOWN_OWNER})")

            if top == "PySide6":
                if layer in ("core", "adapters"):
                    violations.append(f"{rel_posix}: la capa {layer} no puede importar PySide6")
                elif layer == "app" and not (len(parts) > 1 and parts[1] == "QtCore"):
                    violations.append(f"{rel_posix}: app solo puede importar PySide6.QtCore")

            if top == PACKAGE and layer is not None and len(parts) > 1:
                target = parts[1]
                if target in ALLOWED_INTERNAL and target != layer:
                    if target not in ALLOWED_INTERNAL[layer]:
                        violations.append(
                            f"{rel_posix}: la capa {layer} no puede importar {target}"
                        )
    return violations


def test_codigo_real_respeta_las_capas():
    assert find_violations(SRC) == []


def test_el_verificador_detecta_infracciones(tmp_path: Path):
    """Prueba del verificador: construye un paquete con infracciones conocidas."""
    pkg = tmp_path / PACKAGE
    files = {
        "core/malo_qt.py": "from PySide6.QtCore import QObject\n",
        "core/malo_ui.py": "from ..ui import ventana\n",
        "adapters/markitdown_engine.py": "import markitdown\n",  # permitido
        "adapters/otro.py": "from markitdown import MarkItDown\n",
        "app/cola_ok.py": "from PySide6.QtCore import Signal\nfrom ..core import models\n",
        "app/cola_mal.py": "from PySide6.QtWidgets import QWidget\n",
        "ui/mala.py": f"import markitdown\nfrom {PACKAGE}.adapters import x\n",
        "ui/buena.py": "from ..app import cola\nfrom ..core import models\n",
        "__main__.py": f"from {PACKAGE}.adapters import x\nfrom {PACKAGE}.ui import y\n",
    }
    for rel, code in files.items():
        target = pkg / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(code, encoding="utf-8")

    problems = "\n".join(find_violations(pkg))

    assert "core/malo_qt.py" in problems
    assert "core/malo_ui.py" in problems
    assert "adapters/otro.py: importa markitdown" in problems
    assert "app/cola_mal.py" in problems
    assert "ui/mala.py: importa markitdown" in problems
    assert "ui/mala.py: la capa ui no puede importar adapters" in problems
    # Lo permitido no debe marcarse
    assert "adapters/markitdown_engine.py:" not in problems
    assert "app/cola_ok.py" not in problems
    assert "ui/buena.py" not in problems
    assert "__main__.py" not in problems
