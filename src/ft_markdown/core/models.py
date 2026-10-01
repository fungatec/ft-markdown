"""Modelos de datos del nucleo: resultado de una conversion y trabajo de la cola."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path

from .errors import ConversionError


@dataclass(frozen=True)
class ConversionResult:
    """Markdown obtenido de un documento."""

    source: Path
    markdown: str
    title: str | None = None


class JobState(Enum):
    """Los cinco estados visibles de un trabajo (FR-005)."""

    PENDING = "pending"
    CONVERTING = "converting"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


_ALLOWED: dict[JobState, frozenset[JobState]] = {
    JobState.PENDING: frozenset({JobState.CONVERTING, JobState.CANCELLED}),
    JobState.CONVERTING: frozenset({JobState.DONE, JobState.ERROR, JobState.CANCELLED}),
    JobState.DONE: frozenset(),
    JobState.ERROR: frozenset(),
    JobState.CANCELLED: frozenset(),
}


@dataclass(frozen=True)
class ConversionJob:
    """Un archivo en la cola. Es inmutable: cada transicion devuelve un trabajo nuevo.

    Solo se permiten estas transiciones: pendiente -> convirtiendo -> listo | error, y
    cancelar mientras este pendiente o convirtiendo. Cualquier otra lanza ValueError.
    """

    source: Path
    state: JobState = JobState.PENDING
    result: ConversionResult | None = None
    error: ConversionError | None = None

    @property
    def is_finished(self) -> bool:
        return not _ALLOWED[self.state]

    def start(self) -> ConversionJob:
        return self._to(JobState.CONVERTING)

    def finish(self, result: ConversionResult) -> ConversionJob:
        return self._to(JobState.DONE, result=result)

    def fail(self, error: ConversionError) -> ConversionJob:
        return self._to(JobState.ERROR, error=error)

    def cancel(self) -> ConversionJob:
        return self._to(JobState.CANCELLED)

    def _to(self, state: JobState, **changes: object) -> ConversionJob:
        if state not in _ALLOWED[self.state]:
            raise ValueError(f"Transicion no permitida: {self.state.value} -> {state.value}")
        return replace(self, state=state, **changes)
