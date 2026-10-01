"""Cola de conversion en segundo plano (FR-005, HU-3, plan seccion 2).

Ejecuta los archivos en un `QThreadPool` (maximo 2 a la vez para no saturar la memoria con PDF
grandes). Todo el estado (`ConversionJob`) se modifica solo en el hilo de la interfaz: los hilos de
trabajo unicamente avisan con senales. Un fallo aislado nunca detiene al resto del lote.

Cancelacion: los trabajos pendientes no llegan a arrancar. El que ya esta convirtiendo no se puede
interrumpir (MarkItDown no lo permite): termina, su resultado se descarta y queda CANCELLED.
"""

from __future__ import annotations

import threading
from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal, Slot

from ft_markdown.core.engine import ConversionEngine
from ft_markdown.core.errors import ConversionError, ErrorKind
from ft_markdown.core.models import ConversionJob, JobState

MAX_CONCURRENT = 2


class _Worker(QRunnable):
    """Convierte un archivo y avisa a la cola; nunca deja escapar una excepcion."""

    def __init__(self, queue: ConversionQueue, index: int, path: Path) -> None:
        super().__init__()
        self._queue = queue
        self._index = index
        self._path = path

    def run(self) -> None:
        queue, index = self._queue, self._index
        if queue._is_cancelled(index):  # cancelado antes de arrancar: no se convierte
            return
        queue._started.emit(index)
        try:
            result = queue._engine.convert_file(self._path)
        except ConversionError as error:
            queue._failed.emit(index, error)
        except Exception as exc:  # noqa: BLE001 - un fallo inesperado no debe frenar la cola
            error = ConversionError(str(exc), kind=ErrorKind.UNKNOWN, source=self._path)
            queue._failed.emit(index, error)
        else:
            queue._succeeded.emit(index, result)


class ConversionQueue(QObject):
    """Cola de trabajos de conversion con estado individual y cancelacion."""

    job_changed = Signal(int, object)  # indice, ConversionJob actualizado
    progress = Signal(int, int)  # trabajos terminados, total
    batch_finished = Signal()  # todos los trabajos conocidos terminaron

    _started = Signal(int)
    _succeeded = Signal(int, object)
    _failed = Signal(int, object)

    def __init__(
        self,
        engine: ConversionEngine,
        *,
        max_concurrent: int = MAX_CONCURRENT,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._engine = engine
        self._jobs: list[ConversionJob] = []
        self._cancelled: set[int] = set()
        self._lock = threading.Lock()
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(max_concurrent)
        queued = Qt.ConnectionType.QueuedConnection
        self._started.connect(self._on_started, queued)
        self._succeeded.connect(self._on_succeeded, queued)
        self._failed.connect(self._on_failed, queued)

    @property
    def jobs(self) -> tuple[ConversionJob, ...]:
        return tuple(self._jobs)

    @property
    def is_idle(self) -> bool:
        return all(job.is_finished for job in self._jobs)

    def add_files(self, paths: Iterable[Path]) -> None:
        """Agrega archivos a la cola y los pone a convertir."""
        for path in paths:
            index = len(self._jobs)
            job = ConversionJob(Path(path))
            self._jobs.append(job)
            self.job_changed.emit(index, job)
            self._pool.start(_Worker(self, index, job.source))

    def cancel_all(self) -> None:
        """Cancela todo lo que no ha terminado (ver nota de cancelacion en el modulo)."""
        for index, job in enumerate(self._jobs):
            if not job.is_finished:
                self._cancel(index)

    def cancel(self, index: int) -> None:
        if not self._jobs[index].is_finished:
            self._cancel(index)

    def _cancel(self, index: int) -> None:
        with self._lock:
            self._cancelled.add(index)
        job = self._jobs[index]
        if job.state is JobState.PENDING:  # los pendientes se cancelan al instante
            self._update(index, job.cancel())
        # Si esta convirtiendo, se marca como cancelado cuando el motor devuelva el control.

    def _is_cancelled(self, index: int) -> bool:
        with self._lock:
            return index in self._cancelled

    def _update(self, index: int, job: ConversionJob) -> None:
        self._jobs[index] = job
        self.job_changed.emit(index, job)
        done = sum(1 for j in self._jobs if j.is_finished)
        self.progress.emit(done, len(self._jobs))
        if done == len(self._jobs):
            self.batch_finished.emit()

    @Slot(int)
    def _on_started(self, index: int) -> None:
        job = self._jobs[index]
        if job.state is JobState.PENDING:
            self._update(index, job.start())

    @Slot(int, object)
    def _on_succeeded(self, index: int, result: object) -> None:
        job = self._jobs[index]
        if job.is_finished:
            return
        if self._is_cancelled(index):
            self._update(index, job.cancel())  # el resultado se descarta
        else:
            self._update(index, job.finish(result))  # type: ignore[arg-type]

    @Slot(int, object)
    def _on_failed(self, index: int, error: object) -> None:
        job = self._jobs[index]
        if job.is_finished:
            return
        if self._is_cancelled(index):
            self._update(index, job.cancel())
        else:
            self._update(index, job.fail(error))  # type: ignore[arg-type]
