"""Monitor de conectividad (FR-008, P3, plan seccion 2).

Consulta periodicamente una sonda (`probe`) y avisa con `status_changed` solo cuando el estado
cambia, para que la interfaz habilite o deshabilite las funciones en linea. La consulta corre en un
hilo aparte y nunca se solapa con otra, asi la ventana no se congela aunque la red tarde.

La sonda por defecto solo abre y cierra una conexion TCP con resolutores DNS publicos: no envia
datos ni identifica al usuario (P11, NFR-004). Con el intervalo por defecto (5 s) y el tiempo
limite de la sonda (3 s), un cambio se detecta en menos de 10 s.
"""

from __future__ import annotations

import socket
import threading
from collections.abc import Callable, Iterable

from PySide6.QtCore import QObject, Qt, QTimer, Signal

DEFAULT_INTERVAL_MS = 5_000
PROBE_TIMEOUT_S = 3.0
PROBE_HOSTS: tuple[tuple[str, int], ...] = (("1.1.1.1", 443), ("8.8.8.8", 443))


def tcp_probe(
    hosts: Iterable[tuple[str, int]] = PROBE_HOSTS, timeout: float = PROBE_TIMEOUT_S
) -> bool:
    """Devuelve True si alguno de los destinos acepta una conexion TCP."""
    for host, port in hosts:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


class ConnectivityMonitor(QObject):
    """Vigila si hay internet y avisa de cada cambio de estado."""

    status_changed = Signal(bool)  # True: en linea; False: sin conexion

    _probed = Signal(bool)

    def __init__(
        self,
        probe: Callable[[], bool] = tcp_probe,
        *,
        interval_ms: int = DEFAULT_INTERVAL_MS,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._probe = probe
        self._online: bool | None = None
        self._busy = threading.Lock()
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.check_now)
        self._probed.connect(self._on_probed, Qt.ConnectionType.QueuedConnection)

    @property
    def is_online(self) -> bool | None:
        """Ultimo estado conocido; None antes de la primera consulta."""
        return self._online

    def start(self) -> None:
        """Consulta de inmediato y despues cada intervalo."""
        self._timer.start()
        self.check_now()

    def stop(self) -> None:
        self._timer.stop()

    def check_now(self) -> None:
        """Lanza una consulta en segundo plano, salvo que ya haya una en curso."""
        if not self._busy.acquire(blocking=False):
            return
        threading.Thread(target=self._run_probe, name="ft-connectivity", daemon=True).start()

    def _run_probe(self) -> None:
        try:
            online = bool(self._probe())
        except Exception:  # noqa: BLE001 - una sonda rota equivale a no tener conexion
            online = False
        try:
            self._probed.emit(online)  # antes de liberar: los resultados llegan en orden
        finally:
            self._busy.release()

    def _on_probed(self, online: bool) -> None:
        if online != self._online:
            self._online = online
            self.status_changed.emit(online)
