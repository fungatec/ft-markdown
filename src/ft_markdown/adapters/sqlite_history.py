"""Historial de conversiones en SQLite (history.sqlite). Solo metadatos, nunca contenido."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from ..core.history import MAX_ENTRIES, HistoryEntry, HistoryStatus

_CREAR = """
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    title TEXT,
    status TEXT NOT NULL,
    converted_at TEXT NOT NULL
)
"""


class SqliteHistoryStore:
    def __init__(self, path: Path, max_entries: int = MAX_ENTRIES) -> None:
        self._path = path
        self._max = max_entries
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._conectar() as conexion:
            conexion.execute(_CREAR)

    def add(self, entry: HistoryEntry) -> None:
        with self._conectar() as conexion:
            conexion.execute(
                "INSERT INTO history (source, title, status, converted_at) VALUES (?, ?, ?, ?)",
                (entry.source, entry.title, entry.status.value, entry.converted_at.isoformat()),
            )
            conexion.execute(
                "DELETE FROM history WHERE id NOT IN "
                "(SELECT id FROM history ORDER BY id DESC LIMIT ?)",
                (self._max,),
            )

    def recent(self, limit: int | None = None) -> list[HistoryEntry]:
        consulta = "SELECT source, title, status, converted_at FROM history ORDER BY id DESC"
        parametros: tuple = ()
        if limit is not None:
            consulta += " LIMIT ?"
            parametros = (limit,)
        with self._conectar() as conexion:
            filas = conexion.execute(consulta, parametros).fetchall()
        return [
            HistoryEntry(s, t, HistoryStatus(e), datetime.fromisoformat(f)) for s, t, e, f in filas
        ]

    def clear(self) -> None:
        with self._conectar() as conexion:
            conexion.execute("DELETE FROM history")

    def _conectar(self):
        """Una conexion por operacion: la cola de conversion usa varios hilos."""
        return _Conexion(self._path)


class _Conexion:
    """Contexto que confirma la transaccion y siempre cierra la conexion."""

    def __init__(self, path: Path) -> None:
        self._conexion = sqlite3.connect(path)

    def __enter__(self) -> sqlite3.Connection:
        return self._conexion

    def __exit__(self, tipo, valor, traza) -> None:
        with closing(self._conexion):
            if tipo is None:
                self._conexion.commit()
            else:
                self._conexion.rollback()
