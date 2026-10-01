import sqlite3
from datetime import UTC, datetime

from ft_markdown.adapters.sqlite_history import SqliteHistoryStore
from ft_markdown.core.history import HistoryEntry, HistoryStatus


def _entrada(n: int, estado: HistoryStatus = HistoryStatus.DONE) -> HistoryEntry:
    return HistoryEntry(
        source=f"C:\\docs\\informe {n}.pdf",
        title=f"Informe {n}",
        status=estado,
        converted_at=datetime(2026, 10, 1, 12, 0, n % 60, tzinfo=UTC),
    )


def test_historial_vacio(tmp_path):
    assert SqliteHistoryStore(tmp_path / "history.sqlite").recent() == []


def test_las_entradas_mas_recientes_van_primero(tmp_path):
    h = SqliteHistoryStore(tmp_path / "history.sqlite")
    for n in range(3):
        h.add(_entrada(n))
    assert [e.title for e in h.recent()] == ["Informe 2", "Informe 1", "Informe 0"]


def test_se_conserva_el_estado_la_fecha_y_el_origen(tmp_path):
    h = SqliteHistoryStore(tmp_path / "history.sqlite")
    original = _entrada(7, HistoryStatus.ERROR)
    h.add(original)
    assert h.recent() == [original]


def test_solo_se_guardan_las_ultimas_50(tmp_path):
    h = SqliteHistoryStore(tmp_path / "history.sqlite")
    for n in range(60):
        h.add(_entrada(n))
    entradas = h.recent()
    assert len(entradas) == 50
    assert entradas[0].title == "Informe 59" and entradas[-1].title == "Informe 10"


def test_el_limite_es_configurable(tmp_path):
    h = SqliteHistoryStore(tmp_path / "history.sqlite", max_entries=3)
    for n in range(5):
        h.add(_entrada(n))
    assert len(h.recent()) == 3


def test_recent_acepta_un_limite(tmp_path):
    h = SqliteHistoryStore(tmp_path / "history.sqlite")
    for n in range(5):
        h.add(_entrada(n))
    assert len(h.recent(limit=2)) == 2


def test_clear_borra_todo(tmp_path):
    h = SqliteHistoryStore(tmp_path / "history.sqlite")
    h.add(_entrada(1))
    h.clear()
    assert h.recent() == []


def test_persiste_entre_instancias_y_crea_la_carpeta(tmp_path):
    ruta = tmp_path / "FT Markdown" / "history.sqlite"
    SqliteHistoryStore(ruta).add(_entrada(1))
    assert len(SqliteHistoryStore(ruta).recent()) == 1


def test_no_se_guarda_contenido_de_documentos(tmp_path):
    """P4/P12: la base solo tiene ruta, titulo, estado y fecha; nunca el Markdown."""
    ruta = tmp_path / "history.sqlite"
    SqliteHistoryStore(ruta).add(_entrada(1))
    with sqlite3.connect(ruta) as conexion:
        columnas = [f[1] for f in conexion.execute("PRAGMA table_info(history)")]
    assert sorted(columnas) == sorted(["id", "source", "title", "status", "converted_at"])
