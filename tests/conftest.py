"""Fixtures de limpieza para objetos con hilos (T013/T014, ajuste de cierre ordenado).

Una cola o un monitor que queda vivo al terminar un test deja hilos que emiten senales sobre
objetos Qt ya destruidos (access violation intermitente al final de pytest). Estas fabricas los
cierran con `shutdown()` al terminar cada test.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from ft_markdown.app.connectivity import ConnectivityMonitor  # noqa: E402
from ft_markdown.app.conversion_queue import ConversionQueue  # noqa: E402


@pytest.fixture
def queue_factory(qtbot):
    creadas: list[ConversionQueue] = []

    def crear(*args, **kwargs) -> ConversionQueue:
        cola = ConversionQueue(*args, **kwargs)
        creadas.append(cola)
        return cola

    yield crear
    for cola in creadas:
        assert cola.shutdown(timeout_ms=10_000), "la cola no cerro a tiempo"


@pytest.fixture
def monitor_factory(qtbot):
    creados: list[ConnectivityMonitor] = []

    def crear(*args, **kwargs) -> ConnectivityMonitor:
        monitor = ConnectivityMonitor(*args, **kwargs)
        creados.append(monitor)
        return monitor

    yield crear
    for monitor in creados:
        assert monitor.shutdown(timeout_ms=10_000), "el monitor no cerro a tiempo"
