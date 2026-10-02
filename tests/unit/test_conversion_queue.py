"""T013 - ConversionQueue: estados, progreso, cancelacion y aislamiento de fallos (FR-005)."""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path

from PySide6.QtCore import Qt

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from ft_markdown.app.conversion_queue import ConversionQueue  # noqa: E402
from ft_markdown.core.errors import ConversionError, ErrorKind  # noqa: E402
from ft_markdown.core.models import ConversionResult, JobState  # noqa: E402


class FakeEngine:
    """Motor falso: 'bad' falla con ConversionError, 'boom' con una excepcion inesperada."""

    def __init__(self, gate: threading.Event | None = None, delay: float = 0.0) -> None:
        self.gate = gate
        self.delay = delay
        self.calls: list[str] = []
        self.active = 0
        self.max_active = 0
        self._lock = threading.Lock()

    def convert_file(self, path: Path) -> ConversionResult:
        with self._lock:
            self.calls.append(path.name)
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            if self.gate is not None:
                self.gate.wait(timeout=5)
            time.sleep(self.delay)
            if path.stem == "bad":
                raise ConversionError("dañado", kind=ErrorKind.CORRUPT_FILE, source=path)
            if path.stem == "boom":
                raise RuntimeError("fallo inesperado")
            return ConversionResult(source=path, markdown=f"# {path.stem}")
        finally:
            with self._lock:
                self.active -= 1

    def convert_url(self, url: str) -> ConversionResult:  # pragma: no cover
        raise NotImplementedError


def _paths(*names: str) -> list[Path]:
    return [Path(n) for n in names]


def test_convierte_un_lote_y_reporta_progreso(qtbot, queue_factory):
    queue = queue_factory(FakeEngine())
    progress: list[tuple[int, int]] = []
    queue.progress.connect(lambda d, t: progress.append((d, t)))
    with qtbot.waitSignal(queue.batch_finished, timeout=5000):
        queue.add_files(_paths("a.pdf", "b.docx", "c.xlsx"))
    assert [j.state for j in queue.jobs] == [JobState.DONE] * 3
    assert queue.jobs[0].result.markdown == "# a"
    assert progress[-1] == (3, 3)
    assert [d for d, _ in progress] == sorted(d for d, _ in progress)
    assert queue.is_idle


def test_un_archivo_danado_en_un_lote_de_10_no_detiene_los_otros_9(qtbot, queue_factory):
    queue = queue_factory(FakeEngine())
    names = [f"f{i}.pdf" for i in range(4)] + ["bad.pdf"] + [f"g{i}.pdf" for i in range(5)]
    with qtbot.waitSignal(queue.batch_finished, timeout=5000):
        queue.add_files(_paths(*names))
    states = [j.state for j in queue.jobs]
    assert states.count(JobState.DONE) == 9
    assert states.count(JobState.ERROR) == 1
    assert queue.jobs[4].error.kind is ErrorKind.CORRUPT_FILE


def test_una_excepcion_inesperada_se_convierte_en_error_y_la_cola_sigue(qtbot, queue_factory):
    queue = queue_factory(FakeEngine())
    with qtbot.waitSignal(queue.batch_finished, timeout=5000):
        queue.add_files(_paths("boom.pdf", "ok.pdf"))
    assert queue.jobs[0].state is JobState.ERROR
    assert queue.jobs[0].error.kind is ErrorKind.UNKNOWN
    assert queue.jobs[1].state is JobState.DONE


def test_nunca_hay_mas_de_dos_conversiones_simultaneas(qtbot, queue_factory):
    engine = FakeEngine(delay=0.05)
    queue = queue_factory(engine)
    with qtbot.waitSignal(queue.batch_finished, timeout=10000):
        queue.add_files(_paths(*[f"f{i}.pdf" for i in range(8)]))
    assert 1 <= engine.max_active <= 2


def test_cancelar_evita_arrancar_pendientes_y_descarta_el_que_esta_en_curso(qtbot, queue_factory):
    gate = threading.Event()
    engine = FakeEngine(gate=gate)
    queue = queue_factory(engine)
    queue.add_files(_paths("a.pdf", "b.pdf", "c.pdf", "d.pdf"))
    qtbot.waitUntil(
        lambda: sum(j.state is JobState.CONVERTING for j in queue.jobs) == 2, timeout=5000
    )
    with qtbot.waitSignal(queue.batch_finished, timeout=5000):
        queue.cancel_all()
        gate.set()
    assert [j.state for j in queue.jobs] == [JobState.CANCELLED] * 4
    assert all(j.result is None for j in queue.jobs)  # el resultado en curso se descarto
    assert len(engine.calls) == 2  # los pendientes nunca llegaron al motor


def test_cancelar_un_solo_trabajo_pendiente(qtbot, queue_factory):
    gate = threading.Event()
    queue = queue_factory(FakeEngine(gate=gate))
    queue.add_files(_paths("a.pdf", "b.pdf", "c.pdf"))
    qtbot.waitUntil(
        lambda: sum(j.state is JobState.CONVERTING for j in queue.jobs) == 2, timeout=5000
    )
    queue.cancel(2)
    with qtbot.waitSignal(queue.batch_finished, timeout=5000):
        gate.set()
    assert [j.state for j in queue.jobs] == [JobState.DONE, JobState.DONE, JobState.CANCELLED]


def test_se_pueden_agregar_archivos_con_la_cola_en_marcha(qtbot, queue_factory):
    queue = queue_factory(FakeEngine(delay=0.05))
    queue.add_files(_paths("a.pdf"))
    with qtbot.waitSignal(queue.batch_finished, timeout=5000):
        queue.add_files(_paths("b.pdf"))
    assert len(queue.jobs) == 2
    assert all(j.state is JobState.DONE for j in queue.jobs)


def test_emite_job_changed_en_cada_transicion(qtbot, queue_factory):
    queue = queue_factory(FakeEngine())
    seen: list[tuple[int, JobState]] = []
    queue.job_changed.connect(lambda i, j: seen.append((i, j.state)))
    with qtbot.waitSignal(queue.batch_finished, timeout=5000):
        queue.add_files(_paths("a.pdf"))
    assert seen == [(0, JobState.PENDING), (0, JobState.CONVERTING), (0, JobState.DONE)]


# --- Cierre ordenado (ajuste T013) -------------------------------------------------------------


def _excepciones_de_hilos():
    """Captura las excepciones que escapan de hilos (un worker nunca debe dejar escapar una)."""
    vistas: list[BaseException] = []
    anterior = threading.excepthook
    threading.excepthook = lambda args: vistas.append(args.exc_value)
    return vistas, lambda: setattr(threading, "excepthook", anterior)


def test_cerrar_con_una_conversion_en_curso_espera_y_no_deja_hilos(qtbot, queue_factory):
    gate = threading.Event()
    engine = FakeEngine(gate=gate)
    queue = queue_factory(engine)
    queue.add_files(_paths("a.pdf", "b.pdf", "c.pdf", "d.pdf"))
    qtbot.waitUntil(
        lambda: sum(j.state is JobState.CONVERTING for j in queue.jobs) == 2, timeout=5000
    )
    threading.Timer(0.2, gate.set).start()  # el motor termina mientras shutdown espera

    assert queue.shutdown(timeout_ms=5000) is True
    assert queue._pool.activeThreadCount() == 0
    assert engine.active == 0
    assert len(engine.calls) == 2  # los pendientes nunca llegaron al motor
    assert all(j.state is JobState.CANCELLED for j in queue.jobs)


def test_tras_cerrar_no_se_emiten_senales_aunque_el_motor_termine_tarde(qtbot, queue_factory):
    gate = threading.Event()
    queue = queue_factory(FakeEngine(gate=gate))
    cambios: list[int] = []
    internas: list[str] = []
    queue.add_files(_paths("a.pdf"))
    qtbot.waitUntil(lambda: queue.jobs[0].state is JobState.CONVERTING, timeout=5000)
    queue.job_changed.connect(lambda i, j: cambios.append(i))
    queue._succeeded.connect(lambda *a: internas.append("ok"), Qt.ConnectionType.DirectConnection)
    queue._failed.connect(lambda *a: internas.append("fallo"), Qt.ConnectionType.DirectConnection)

    assert queue.shutdown(timeout_ms=50) is False  # el motor no termina dentro del plazo
    antes = list(cambios)
    gate.set()  # ahora termina: sus resultados no deben llegar a nadie
    queue._pool.waitForDone(5000)
    qtbot.wait(100)
    assert internas == []
    assert cambios == antes


def test_un_worker_tardio_no_toca_una_cola_destruida(qtbot):
    from shiboken6 import delete

    vistas, restaurar = _excepciones_de_hilos()
    gate = threading.Event()
    engine = FakeEngine(gate=gate)
    queue = ConversionQueue(engine)
    try:
        queue.add_files(_paths("a.pdf", "b.pdf"))
        qtbot.waitUntil(lambda: engine.active == 2, timeout=5000)
        assert queue.shutdown(timeout_ms=50) is False
        threading.Timer(0.2, gate.set).start()
        delete(queue)  # el destructor del pool espera al worker, que ya no debe emitir nada
        qtbot.wait(100)
    finally:
        restaurar()
    assert engine.active == 0
    assert vistas == []


def test_cerrar_es_idempotente_y_no_admite_trabajos_nuevos(qtbot, queue_factory):
    queue = queue_factory(FakeEngine())
    assert queue.shutdown() is True
    assert queue.shutdown() is True
    queue.add_files(_paths("a.pdf"))
    assert queue.jobs == ()
