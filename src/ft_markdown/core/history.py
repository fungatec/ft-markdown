"""Historial de conversiones (FR-011).

Solo se guarda de donde vino el documento, su titulo, el resultado y la fecha. Nunca el
contenido: asi no se duplican documentos que pueden ser sensibles (P4). Para reabrir una
entrada se vuelve a convertir el original.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

MAX_ENTRIES = 50


class HistoryStatus(Enum):
    DONE = "done"
    ERROR = "error"


@dataclass(frozen=True)
class HistoryEntry:
    source: str  # ruta del archivo o URL
    title: str | None
    status: HistoryStatus
    converted_at: datetime


class HistoryStore(Protocol):
    def add(self, entry: HistoryEntry) -> None: ...

    def recent(self, limit: int | None = None) -> list[HistoryEntry]: ...

    def clear(self) -> None: ...
