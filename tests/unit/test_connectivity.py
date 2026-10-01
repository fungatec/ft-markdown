"""T014 - ConnectivityMonitor: detecta en linea / sin conexion en menos de 10 s (FR-008, P3)."""

from __future__ import annotations

import os
import socket
import threading
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from ft_markdown.app.connectivity import (  # noqa: E402
    DEFAULT_INTERVAL_MS,
    PROBE_TIMEOUT_S,
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
    assert DEFAULT_INTERVAL_MS == 5_000
    assert DEFAULT_INTERVAL_MS / 1000 + PROBE_TIMEOUT_S < 10


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


def test_check_now_consulta_de_inmediato_mientras_esta_activo(qtbot):
    probe = FakeProbe(True)
    monitor = ConnectivityMonitor(probe, interval_ms=60_000)
    with qtbot.waitSignal(monitor.status_changed, timeout=2000):
        monitor.start()
    assert probe.calls == 1

    def asked_again() -> bool:
        # La primera consulta se marca como terminada justo despues de avisar; hasta entonces
        # check_now() se ignora para no solapar consultas, asi que se reintenta.
        monitor.check_now()
        return probe.calls == 2

    qtbot.waitUntil(asked_again, timeout=2000)
    monitor.stop()


def test_detenido_no_llama_a_la_sonda(qtbot):
    probe = FakeProbe(True)
    monitor = ConnectivityMonitor(probe, interval_ms=20)
    assert not monitor.is_active
    monitor.check_now()  # sin start(): no debe abrir ningun socket
    qtbot.wait(150)
    assert probe.calls == 0
    assert monitor.is_online is None


def test_start_y_stop_repetidos_son_seguros(qtbot):
    probe = FakeProbe(True)
    monitor = ConnectivityMonitor(probe, interval_ms=60_000)
    seen: list[bool] = []
    monitor.status_changed.connect(seen.append)
    monitor.start()
    monitor.start()  # el segundo start no lanza otra consulta inmediata
    qtbot.waitUntil(lambda: seen == [True], timeout=2000)
    qtbot.wait(100)
    assert probe.calls == 1
    monitor.stop()
    monitor.stop()
    assert not monitor.is_active
    assert monitor.is_online is None
    with qtbot.waitSignal(monitor.status_changed, timeout=2000) as blocker:
        monitor.start()  # al reanudar se vuelve a informar el estado
    assert blocker.args == [True]
    monitor.stop()


def test_tras_stop_no_llegan_senales_atrasadas(qtbot):
    probe = FakeProbe(True, delay=0.2)
    monitor = ConnectivityMonitor(probe, interval_ms=60_000)
    seen: list[bool] = []
    monitor.status_changed.connect(seen.append)
    monitor.start()
    qtbot.waitUntil(lambda: probe.active == 1, timeout=2000)
    monitor.stop()  # la consulta en curso termina, pero su resultado se descarta
    qtbot.wait(400)
    assert probe.calls == 1
    assert seen == []
    assert monitor.is_online is None


def test_una_consulta_vieja_no_bloquea_la_de_un_nuevo_start(qtbot):
    probe = FakeProbe(True, delay=0.3)
    monitor = ConnectivityMonitor(probe, interval_ms=60_000)
    monitor.start()
    qtbot.waitUntil(lambda: probe.active == 1, timeout=2000)
    monitor.stop()
    with qtbot.waitSignal(monitor.status_changed, timeout=2000):
        monitor.start()  # comprueba de inmediato aunque la consulta anterior siga en curso
    assert probe.calls == 2
    monitor.stop()


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
