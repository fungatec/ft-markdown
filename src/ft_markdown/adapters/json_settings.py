"""Almacen de ajustes en un archivo JSON (settings.json)."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, fields
from pathlib import Path

from ..core.settings import THEMES, Settings


class JsonSettingsStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> Settings:
        """Lee los ajustes. Un archivo ausente o danado nunca impide abrir la app."""
        try:
            crudo = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(crudo, dict):
                raise ValueError("se esperaba un objeto JSON")
        except FileNotFoundError:
            return Settings()
        except (OSError, ValueError):
            self._guardar_copia_del_danado()
            return Settings()
        return _desde_dict(crudo)

    def save(self, settings: Settings) -> None:
        """Escritura atomica: se escribe un temporal y se reemplaza, para no dejar medio archivo."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporal = tempfile.mkstemp(dir=self._path.parent, suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as archivo:
                json.dump(asdict(settings), archivo, ensure_ascii=False, indent=2)
            os.replace(temporal, self._path)
        except BaseException:
            Path(temporal).unlink(missing_ok=True)
            raise

    def _guardar_copia_del_danado(self) -> None:
        try:
            os.replace(self._path, self._path.with_name(self._path.name + ".bak"))
        except OSError:
            pass


def _desde_dict(crudo: dict) -> Settings:
    """Construye Settings ignorando claves desconocidas y valores de tipo invalido."""
    defecto = Settings()
    valores = {}
    for campo in fields(Settings):
        if campo.name not in crudo:
            continue
        valor = crudo[campo.name]
        if isinstance(getattr(defecto, campo.name), bool):
            valido = isinstance(valor, bool)
        else:
            valido = isinstance(valor, str) or (valor is None and campo.name in _OPCIONALES)
        if campo.name == "theme":
            valido = valor in THEMES
        if valido:
            valores[campo.name] = valor
    return Settings(**valores)


_OPCIONALES = {"output_dir", "last_update_check"}
