"""Monitor de conectividad (FR-008, P3, plan seccion 2).

El monitor nace detenido y no toca la red hasta `start()`: solo debe estar activo mientras haya
una funcion en linea visible (URL, YouTube, audio), porque cada conexion necesita un motivo
visible para el usuario (P11, NFR-004). La interfaz llama `start()` al mostrar esas funciones y
`stop()` al ocultarlas.

Mientras esta activo, comprueba de inmediato y despues cada 5 s; con el tiempo limite de la sonda
(3 s), un cambio se detecta en menos de 10 s. Avisa con `status_changed` solo cuando el estado
cambia. La consulta corre en un hilo aparte y nunca se solapa con otra de la misma sesion. Al
detenerse, `is_online` vuelve a None y el resultado de una consulta que siga en curso se descarta.

La sonda por defecto solo abre y cierra una conexion TCP con resolutores DNS publicos: no envia
datos ni identifica al usuario.
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
    """Vigila si hay internet, solo mientras esta activo, y avisa de cada cambio de estado."""

    status_changed = Signal(bool)  # True: en linea; False: sin conexion

    _probed = Signal(int, bool)  # sesion que lanzo la consulta, resultado

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
        self._active = False
        self._session = 0  # cambia en cada start/stop; invalida las consultas anteriores
        self._in_flight: set[int] = set()
        self._lock = threading.Lock()
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.check_now)
        self._probed.connect(self._on_probed, Qt.ConnectionType.QueuedConnection)

    @property
    def is_online(self) -> bool | None:
        """Ultimo estado conocido; None si esta detenido o aun no hay respuesta."""
        return self._online

    @property
    def is_active(self) -> bool:
        return self._active

    def start(self) -> None:
        """Comprueba de inmediato y despues cada intervalo. Si ya esta activo, no hace nada."""
        if self._active:
            return
        self._active = True
        with self._lock:
            self._session += 1
        self._timer.start()
        self.check_now()

    def stop(self) -> None:
        """Deja de consultar y olvida el estado. Si ya esta detenido, no hace nada."""
        if not self._active:
            return
        self._active = False
        self._timer.stop()
        with self._lock:
            self._session += 1
        self._online = None

    def check_now(self) -> None:
        """Lanza una consulta en segundo plano si esta activo y no hay otra de esta sesion."""
        if not self._active:
            return
        with self._lock:
            session = self._session
            if session in self._in_flight:
                return
            self._in_flight.add(session)
        threading.Thread(
            target=self._run_probe, args=(session,), name="ft-connectivity", daemon=True
        ).start()

    def _run_probe(self, session: int) -> None:
        try:
            online = bool(self._probe())
        except Exception:  # noqa: BLE001 - una sonda rota equivale a no tener conexion
            online = False
        try:
            self._probed.emit(session, online)  # antes de liberar: los resultados llegan en orden
        finally:
            with self._lock:
                self._in_flight.discard(session)

    def _on_probed(self, session: int, online: bool) -> None:
        if not self._active or session != self._session:
            return  # consulta de una sesion ya detenida: se descarta sin avisar
        if online != self._online:
            self._online = online
            self.status_changed.emit(online)
