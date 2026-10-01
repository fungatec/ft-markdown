"""T014 - ConnectivityMonitor: detecta en linea / sin conexion en menos de 10 s (FR-008, P3)."""

from __future__ import annotations

import os
import socket
import threading
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from ft_markdown.app.connectivity import (  # noqa: E402
    DEFAULT_INTERVAL_MS,
    ConnectivityMonitor,
    tcp_probe,
)


class FakeProbe:
    """Sonda falsa cuyo resultado se cambia desde la prueba; cuenta las consultas."""

    def __init__(self, online: bool, delay: float = 0.0) -> None:
        self.online = online
        self.delay = delay
        self.calls = 0
        self.threads: set[int] = set()
        self.active = 0
        self.max_active = 0
        self._lock = threading.Lock()

    def __call__(self) -> bool:
        with self._lock:
            self.calls += 1
            self.threads.add(threading.get_ident())
            self.active += 1
            self.max_active = max(self.max_active, self.active)
        try:
            time.sleep(self.delay)
            return self.online
        finally:
            with self._lock:
                self.active -= 1


def test_el_intervalo_por_defecto_detecta_cambios_en_menos_de_10_s():
    assert DEFAULT_INTERVAL_MS < 10_000


def test_el_estado_inicial_es_desconocido_hasta_la_primera_consulta(qtbot):
    monitor = ConnectivityMonitor(FakeProbe(True), interval_ms=50)
    assert monitor.is_online is None
    with qtbot.waitSignal(monitor.status_changed, timeout=2000) as blocker:
        monitor.start()
    assert blocker.args == [True]
    assert monitor.is_online is True
    monitor.stop()


def test_detecta_la_perdida_y_la_vuelta_de_la_conexion(qtbot):
    probe = FakeProbe(True)
    monitor = ConnectivityMonitor(probe, interval_ms=50)
    with qtbot.waitSignal(monitor.status_changed, timeout=2000):
        monitor.start()
    with qtbot.waitSignal(monitor.status_changed, timeout=2000) as blocker:
        probe.online = False
    assert blocker.args == [False]
    assert monitor.is_online is False
    with qtbot.waitSignal(monitor.status_changed, timeout=2000) as blocker:
        probe.online = True
    assert blocker.args == [True]
    monitor.stop()


def test_solo_avisa_cuando_el_estado_cambia(qtbot):
    probe = FakeProbe(False)
    monitor = ConnectivityMonitor(probe, interval_ms=20)
    seen: list[bool] = []
    monitor.status_changed.connect(seen.append)
    monitor.start()
    qtbot.waitUntil(lambda: probe.calls >= 5, timeout=2000)
    monitor.stop()
    assert seen == [False]


def test_la_consulta_corre_fuera_del_hilo_de_la_interfaz_y_sin_solaparse(qtbot):
    probe = FakeProbe(True, delay=0.1)
    monitor = ConnectivityMonitor(probe, interval_ms=10)
    monitor.start()
    qtbot.waitUntil(lambda: probe.calls >= 3, timeout=3000)
    monitor.stop()
    assert threading.get_ident() not in probe.threads
    assert probe.max_active == 1


def test_check_now_consulta_de_inmediato(qtbot):
    probe = FakeProbe(True)
    monitor = ConnectivityMonitor(probe, interval_ms=60_000)
    with qtbot.waitSignal(monitor.status_changed, timeout=2000):
        monitor.check_now()
    assert monitor.is_online is True


def test_una_sonda_que_falla_cuenta_como_sin_conexion(qtbot):
    def broken() -> bool:
        raise OSError("red caida")

    monitor = ConnectivityMonitor(broken, interval_ms=50)
    with qtbot.waitSignal(monitor.status_changed, timeout=2000) as blocker:
        monitor.start()
    assert blocker.args == [False]
    monitor.stop()


def test_stop_detiene_las_consultas(qtbot):
    probe = FakeProbe(True)
    monitor = ConnectivityMonitor(probe, interval_ms=20)
    with qtbot.waitSignal(monitor.status_changed, timeout=2000):
        monitor.start()
    monitor.stop()
    qtbot.wait(100)
    calls = probe.calls
    qtbot.wait(150)
    assert probe.calls == calls


def test_tcp_probe_es_verdadero_con_un_servidor_que_acepta():
    server = socket.create_server(("127.0.0.1", 0))
    try:
        port = server.getsockname()[1]
        assert tcp_probe(hosts=(("127.0.0.1", port),), timeout=1.0) is True
    finally:
        server.close()


def test_tcp_probe_es_falso_si_ningun_destino_responde():
    server = socket.create_server(("127.0.0.1", 0))
    port = server.getsockname()[1]
    server.close()  # puerto libre: la conexion se rechaza
    assert tcp_probe(hosts=(("127.0.0.1", port),), timeout=0.5) is False
