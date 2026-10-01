"""ComponentManager: descarga bajo demanda, verificacion y registro (FR-016, T015).

Ninguna prueba usa internet: el descargador es un doble que escribe un zip sintetico.
"""

import hashlib
import io
import zipfile
from pathlib import Path

import pytest

from ft_markdown.app.components import ComponentManager
from ft_markdown.core.components import (
    CancelledError,
    ComponentSpec,
    DeclinedError,
    DownloadError,
    InsufficientSpaceError,
    IntegrityError,
    UnsafeArchiveError,
)


def _zip(entradas: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for nombre, datos in entradas.items():
            z.writestr(nombre, datos)
    return buffer.getvalue()


BUENO = _zip(
    {
        "ffmpeg-x/LICENSE.txt": b"LGPL",
        "ffmpeg-x/bin/ffmpeg.exe": b"EXE",
        "ffmpeg-x/bin/avcodec-62.dll": b"DLL",
        "ffmpeg-x/bin/ffplay.exe": b"no hace falta",
        "ffmpeg-x/doc/ffmpeg.html": b"<html>",
    }
)


def _spec(datos: bytes = BUENO, **cambios) -> ComponentSpec:
    base = {
        "id": "ffmpeg",
        "version": "n8.1.2-test",
        "url": "https://github.com/ejemplo/descarga.zip",
        "sha256": hashlib.sha256(datos).hexdigest(),
        "size_bytes": len(datos),
        "executable": "bin/ffmpeg.exe",
        "include": ("bin/ffmpeg.exe", "bin/*.dll", "LICENSE.txt"),
    }
    base.update(cambios)
    return ComponentSpec(**base)


class Descargador:
    def __init__(self, datos: bytes = BUENO, *, falla: Exception | None = None, cancela=False):
        self.datos = datos
        self.falla = falla
        self.cancela = cancela
        self.llamadas = 0

    def download(self, url, destino: Path, *, progress, cancelled):
        self.llamadas += 1
        destino.write_bytes(self.datos[:10])  # parcial: el gestor debe limpiarlo si algo falla
        if self.falla:
            raise self.falla
        if self.cancela and cancelled():
            raise CancelledError()
        destino.write_bytes(self.datos)
        progress(len(self.datos), len(self.datos))


def _gestor(tmp_path, descargador=None, libre=10**12):
    descargador = descargador or Descargador()
    gestor = ComponentManager(tmp_path / "components", descargador, disk_free=lambda _: libre)
    return gestor, descargador


def _confirma(spec):
    return True


def test_instala_solo_lo_necesario_y_devuelve_el_ejecutable(tmp_path):
    gestor, _ = _gestor(tmp_path)
    exe = gestor.ensure(_spec(), confirm=_confirma)

    assert exe.name == "ffmpeg.exe" and exe.read_bytes() == b"EXE"
    raiz = exe.parent.parent
    assert (raiz / "bin" / "avcodec-62.dll").exists()
    assert (raiz / "LICENSE.txt").exists()
    assert not (raiz / "bin" / "ffplay.exe").exists()
    assert not (raiz / "doc").exists()


def test_deja_un_registro_y_la_siguiente_vez_no_vuelve_a_descargar(tmp_path):
    gestor, descargador = _gestor(tmp_path)
    spec = _spec()
    exe = gestor.ensure(spec, confirm=_confirma)

    assert gestor.executable(spec) == exe
    assert gestor.installed_ids([spec]) == frozenset({"ffmpeg"})
    preguntas = []
    assert gestor.ensure(spec, confirm=lambda s: preguntas.append(s) or True) == exe
    assert descargador.llamadas == 1 and preguntas == []


def test_si_la_persona_no_confirma_no_se_toca_la_red_ni_el_disco(tmp_path):
    gestor, descargador = _gestor(tmp_path)
    with pytest.raises(DeclinedError):
        gestor.ensure(_spec(), confirm=lambda spec: False)
    assert descargador.llamadas == 0
    assert not (tmp_path / "components").exists()


def test_un_hash_distinto_se_rechaza_y_no_queda_nada(tmp_path):
    gestor, _ = _gestor(tmp_path, Descargador(_zip({"x/bin/ffmpeg.exe": b"otro"})))
    spec = _spec()
    with pytest.raises(IntegrityError):
        gestor.ensure(spec, confirm=_confirma)
    assert gestor.executable(spec) is None
    assert list((tmp_path / "components").rglob("*")) == []


def test_cancelar_borra_los_parciales(tmp_path):
    gestor, _ = _gestor(tmp_path, Descargador(cancela=True))
    with pytest.raises(CancelledError):
        gestor.ensure(_spec(), confirm=_confirma, cancelled=lambda: True)
    assert list((tmp_path / "components").rglob("*")) == []


def test_un_fallo_de_red_borra_los_parciales(tmp_path):
    gestor, _ = _gestor(tmp_path, Descargador(falla=DownloadError("sin red")))
    with pytest.raises(DownloadError):
        gestor.ensure(_spec(), confirm=_confirma)
    assert list((tmp_path / "components").rglob("*")) == []


def test_sin_espacio_libre_falla_antes_de_descargar(tmp_path):
    gestor, descargador = _gestor(tmp_path, libre=1000)
    with pytest.raises(InsufficientSpaceError):
        gestor.ensure(_spec(), confirm=_confirma)
    assert descargador.llamadas == 0


def test_el_espacio_libre_se_mide_en_una_carpeta_existente_bajo_la_raiz(tmp_path):
    consultadas = []

    def libre(ruta):
        assert ruta.exists()
        consultadas.append(ruta)
        return 10**12

    gestor = ComponentManager(tmp_path / "components", Descargador(), disk_free=libre)
    gestor.ensure(_spec(), confirm=_confirma)
    assert consultadas and all(tmp_path in (r, *r.parents) for r in consultadas)


@pytest.mark.parametrize(
    "nombre", ["x/bin/../../fuera.dll", "x/bin/..\\..\\fuera.dll", "/abs/bin/fuera.dll"]
)
def test_rutas_peligrosas_dentro_del_zip_se_rechazan(tmp_path, nombre):
    datos = _zip({"x/bin/ffmpeg.exe": b"EXE", nombre: b"malo"})
    gestor, _ = _gestor(tmp_path, Descargador(datos))
    with pytest.raises(UnsafeArchiveError):
        gestor.ensure(_spec(datos), confirm=_confirma)
    assert not (tmp_path / "fuera.dll").exists()
    assert list((tmp_path / "components").rglob("*")) == []


def test_un_zip_sin_el_ejecutable_se_rechaza(tmp_path):
    datos = _zip({"x/LICENSE.txt": b"LGPL"})
    gestor, _ = _gestor(tmp_path, Descargador(datos))
    with pytest.raises(UnsafeArchiveError):
        gestor.ensure(_spec(datos), confirm=_confirma)


def test_un_registro_con_otro_hash_no_cuenta_como_instalado(tmp_path):
    gestor, _ = _gestor(tmp_path)
    spec = _spec()
    exe = gestor.ensure(spec, confirm=_confirma)
    registro = exe.parent.parent / "manifest.json"
    registro.write_text('{"id": "ffmpeg", "version": "otra", "sha256": "0"}', encoding="utf-8")
    assert gestor.executable(spec) is None


def test_si_se_borra_el_ejecutable_se_vuelve_a_considerar_ausente(tmp_path):
    gestor, _ = _gestor(tmp_path)
    spec = _spec()
    gestor.ensure(spec, confirm=_confirma).unlink()
    assert gestor.executable(spec) is None


def test_una_version_nueva_reemplaza_a_la_anterior(tmp_path):
    gestor, _ = _gestor(tmp_path)
    vieja = gestor.ensure(_spec(), confirm=_confirma)
    nueva = gestor.ensure(_spec(version="n9.0.0-test"), confirm=_confirma)
    assert nueva.exists() and not vieja.exists()


def test_informa_el_progreso(tmp_path):
    gestor, _ = _gestor(tmp_path)
    avances = []
    gestor.ensure(_spec(), confirm=_confirma, progress=lambda hecho, total: avances.append(hecho))
    assert avances and avances[-1] == len(BUENO)
