"""UpdateService: seleccion de version, limite de consultas y descarga verificada (T016).

Sin internet: la fuente es un doble en memoria.
"""

import hashlib
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from ft_markdown.app.updater import UpdateService
from ft_markdown.core.settings import Settings
from ft_markdown.core.updates import (
    MAX_INSTALLER_BYTES,
    Asset,
    Release,
    UpdateError,
    UpdateErrorKind,
    UpdateStatus,
)

AHORA = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
CONTENIDO = b"instalador" * 100


def _release(tag, *, prerelease=False, draft=False, con_assets=True, tamano=len(CONTENIDO)):
    version = tag.lstrip("vV").split("+")[0]
    assets = ()
    if con_assets:
        nombre = f"FT-Markdown-Setup-{version}.exe"
        assets = (
            Asset(nombre, f"https://github.com/x/{tag}/i.exe", tamano),
            Asset(nombre + ".sha256", f"https://github.com/x/{tag}/h", 90),
        )
    return Release(tag=tag, prerelease=prerelease, draft=draft, assets=assets)


class Fuente:
    def __init__(self, releases=(), *, error=None, contenido=CONTENIDO, hash_texto=None):
        self.releases = list(releases)
        self.error = error
        self.contenido = contenido
        self.hash_texto = hash_texto
        self.consultas = 0
        self.descargas = 0

    def list_releases(self):
        self.consultas += 1
        if self.error:
            raise self.error
        return self.releases

    def fetch_text(self, asset, max_bytes):
        if self.hash_texto is not None:
            return self.hash_texto
        nombre = asset.name.removesuffix(".sha256")
        return f"{hashlib.sha256(self.contenido).hexdigest()}  {nombre}\n"

    def download(self, asset, destino, *, max_bytes, progress, cancelled):
        self.descargas += 1
        if cancelled():
            raise UpdateError(UpdateErrorKind.CANCELLED)
        destino.write_bytes(self.contenido)
        progress(len(self.contenido), len(self.contenido))


class Almacen:
    def __init__(self, settings=None, *, falla_al_guardar=False):
        self.settings = settings or Settings()
        self.falla_al_guardar = falla_al_guardar
        self.guardados = 0

    def load(self):
        return self.settings

    def save(self, settings):
        if self.falla_al_guardar:
            raise OSError("disco lleno")
        self.settings = settings
        self.guardados += 1


def _servicio(tmp_path, fuente, *, actual="0.1.0", settings=None, **kw):
    almacen = Almacen(settings, **kw)
    servicio = UpdateService(
        fuente, almacen, actual, updates_dir=tmp_path / "updates", now=lambda: AHORA
    )
    return servicio, almacen


def _marca(delta):
    return (AHORA + delta).isoformat()


# --- versiones: nueva, igual y antigua -------------------------------------------------------


def test_version_nueva(tmp_path):
    servicio, almacen = _servicio(tmp_path, Fuente([_release("v1.0.0")]))
    r = servicio.check()
    assert r.status is UpdateStatus.AVAILABLE and r.release.version.text == "1.0.0"
    assert r.release.installer.name == "FT-Markdown-Setup-1.0.0.exe"
    assert r.release.checksum.name == "FT-Markdown-Setup-1.0.0.exe.sha256"
    assert almacen.settings.last_update_check == AHORA.isoformat(timespec="seconds")


def test_version_igual(tmp_path):
    servicio, _ = _servicio(tmp_path, Fuente([_release("v0.1.0")]))
    assert servicio.check().status is UpdateStatus.UP_TO_DATE


def test_la_publicada_es_mas_antigua(tmp_path):
    servicio, _ = _servicio(tmp_path, Fuente([_release("0.0.9")]), actual="0.1.0")
    r = servicio.check()
    assert r.status is UpdateStatus.AHEAD and r.release is None


def test_sin_releases_publicadas_no_hay_nada_que_actualizar(tmp_path):
    servicio, _ = _servicio(tmp_path, Fuente([]))
    assert servicio.check().status is UpdateStatus.UP_TO_DATE


def test_elige_la_mayor_por_semver_no_por_orden_de_la_lista(tmp_path):
    fuente = Fuente([_release("v1.9.0"), _release("v1.10.0"), _release("v1.2.0")])
    servicio, _ = _servicio(tmp_path, fuente)
    assert servicio.check().release.tag == "v1.10.0"


def test_los_borradores_se_ignoran(tmp_path):
    fuente = Fuente([_release("v2.0.0", draft=True), _release("v1.0.0")])
    servicio, _ = _servicio(tmp_path, fuente)
    assert servicio.check().release.tag == "v1.0.0"


# --- preliminares ----------------------------------------------------------------------------


def test_instalada_estable_ignora_los_preliminares(tmp_path):
    fuente = Fuente([_release("v2.0.0-beta.1", prerelease=True), _release("v1.0.0")])
    servicio, _ = _servicio(tmp_path, fuente, actual="0.1.0")
    assert servicio.check().release.tag == "v1.0.0"


def test_instalada_estable_con_solo_preliminares_no_ve_nada(tmp_path):
    fuente = Fuente([_release("v1.0.0-beta.2", prerelease=True)])
    servicio, _ = _servicio(tmp_path, fuente, actual="0.1.0")
    assert servicio.check().status is UpdateStatus.UP_TO_DATE


def test_instalada_preliminar_si_considera_preliminares(tmp_path):
    fuente = Fuente(
        [_release("v1.0.0-beta.2", prerelease=True), _release("v1.0.0-beta.1", prerelease=True)]
    )
    servicio, _ = _servicio(tmp_path, fuente, actual="1.0.0-beta.1")
    r = servicio.check()
    assert r.status is UpdateStatus.AVAILABLE and r.release.tag == "v1.0.0-beta.2"
    assert r.release.prerelease


def test_instalada_preliminar_ve_la_estable_posterior(tmp_path):
    fuente = Fuente([_release("v1.0.0"), _release("v1.0.0-beta.2", prerelease=True)])
    servicio, _ = _servicio(tmp_path, fuente, actual="1.0.0-beta.2")
    assert servicio.check().release.tag == "v1.0.0"


def test_un_tag_con_sufijo_preliminar_cuenta_como_preliminar_aunque_no_este_marcado(tmp_path):
    servicio, _ = _servicio(tmp_path, Fuente([_release("v2.0.0-rc.1")]), actual="0.1.0")
    assert servicio.check().status is UpdateStatus.UP_TO_DATE


# --- tags ininterpretables: error traducido, nunca excepcion ----------------------------------


def test_tag_ininterpretable_es_error_y_no_excepcion(tmp_path):
    servicio, almacen = _servicio(tmp_path, Fuente([_release("latest-build")]))
    r = servicio.check()
    assert r.status is UpdateStatus.FAILED
    assert r.error.kind is UpdateErrorKind.INVALID_VERSION
    assert almacen.settings.last_update_check is not None  # el servidor respondio


def test_un_tag_raro_no_bloquea_las_versiones_validas(tmp_path):
    servicio, _ = _servicio(tmp_path, Fuente([_release("nightly"), _release("v1.0.0")]))
    assert servicio.check().release.tag == "v1.0.0"


def test_la_version_instalada_ininterpretable_es_error(tmp_path):
    servicio, _ = _servicio(tmp_path, Fuente([_release("v1.0.0")]), actual="dev")
    r = servicio.check()
    assert r.status is UpdateStatus.FAILED and r.error.kind is UpdateErrorKind.INVALID_VERSION


def test_version_nueva_sin_los_assets_esperados(tmp_path):
    servicio, _ = _servicio(tmp_path, Fuente([_release("v1.0.0", con_assets=False)]))
    r = servicio.check()
    assert r.status is UpdateStatus.FAILED and r.error.kind is UpdateErrorKind.MISSING_ASSET


# --- desactivado, 24 h y un intento por arranque ----------------------------------------------


def test_desactivado_no_consulta(tmp_path):
    fuente = Fuente([_release("v1.0.0")])
    servicio, almacen = _servicio(tmp_path, fuente, settings=Settings(check_updates=False))
    assert servicio.check().status is UpdateStatus.SKIPPED_DISABLED
    assert fuente.consultas == 0 and almacen.guardados == 0


def test_la_comprobacion_manual_ignora_desactivado_y_el_limite(tmp_path):
    ajustes = Settings(check_updates=False, last_update_check=_marca(-timedelta(minutes=1)))
    fuente = Fuente([_release("v1.0.0")])
    servicio, _ = _servicio(tmp_path, fuente, settings=ajustes)
    assert servicio.check(manual=True).status is UpdateStatus.AVAILABLE
    assert servicio.check(manual=True).status is UpdateStatus.AVAILABLE
    assert fuente.consultas == 2


def test_dentro_de_24_h_no_consulta(tmp_path):
    fuente = Fuente([_release("v1.0.0")])
    ajustes = Settings(last_update_check=_marca(-timedelta(hours=23, minutes=59)))
    servicio, _ = _servicio(tmp_path, fuente, settings=ajustes)
    assert servicio.check().status is UpdateStatus.SKIPPED_RECENT
    assert fuente.consultas == 0


@pytest.mark.parametrize(
    "marca",
    [
        _marca(-timedelta(hours=24)),
        _marca(-timedelta(days=30)),
        _marca(timedelta(days=3)),  # reloj movido: no bloquea para siempre
        "basura",
        "",
        None,
        (AHORA - timedelta(days=30)).replace(tzinfo=None).isoformat(),
    ],
)
def test_pasadas_24_h_o_marca_invalida_si_consulta(tmp_path, marca):
    fuente = Fuente([_release("v1.0.0")])
    servicio, _ = _servicio(tmp_path, fuente, settings=Settings(last_update_check=marca))
    assert servicio.check().status is UpdateStatus.AVAILABLE


def test_un_solo_intento_por_arranque_aunque_falle_sin_conexion(tmp_path):
    fuente = Fuente(error=UpdateError(UpdateErrorKind.NO_CONNECTION))
    servicio, _ = _servicio(tmp_path, fuente)
    assert servicio.check().status is UpdateStatus.FAILED
    assert servicio.check().status is UpdateStatus.SKIPPED_ALREADY_TRIED
    assert fuente.consultas == 1


# --- registro de la consulta -----------------------------------------------------------------


@pytest.mark.parametrize(
    "tipo", [UpdateErrorKind.RATE_LIMIT, UpdateErrorKind.SERVER, UpdateErrorKind.BAD_RESPONSE]
)
def test_si_el_servidor_respondio_se_guarda_la_consulta_aunque_sea_error(tmp_path, tipo):
    servicio, almacen = _servicio(tmp_path, Fuente(error=UpdateError(tipo)))
    r = servicio.check()
    assert r.status is UpdateStatus.FAILED and r.error.kind is tipo
    assert almacen.settings.last_update_check == AHORA.isoformat(timespec="seconds")


def test_si_no_pudo_conectar_no_se_guarda(tmp_path):
    fuente = Fuente(error=UpdateError(UpdateErrorKind.NO_CONNECTION))
    servicio, almacen = _servicio(tmp_path, fuente)
    assert servicio.check().status is UpdateStatus.FAILED
    assert almacen.settings.last_update_check is None and almacen.guardados == 0


def test_guardar_conserva_los_demas_ajustes_y_un_fallo_de_disco_no_rompe(tmp_path):
    base = Settings(theme="light", output_dir="C:/salida")
    servicio, almacen = _servicio(tmp_path, Fuente([_release("v1.0.0")]), settings=base)
    servicio.check()
    assert replace(almacen.settings, last_update_check=None) == base
    servicio2, _ = _servicio(tmp_path, Fuente([_release("v1.0.0")]), falla_al_guardar=True)
    assert servicio2.check().status is UpdateStatus.AVAILABLE


# --- descarga verificada ---------------------------------------------------------------------


def _disponible(tmp_path, fuente):
    servicio, _ = _servicio(tmp_path, fuente)
    return servicio, servicio.check().release


def test_descarga_verifica_y_devuelve_la_ruta(tmp_path):
    servicio, release = _disponible(tmp_path, Fuente([_release("v1.0.0")]))
    avances = []
    ruta = servicio.download(release, progress=lambda h, t: avances.append(h))
    assert ruta == tmp_path / "updates" / "FT-Markdown-Setup-1.0.0.exe"
    assert ruta.read_bytes() == CONTENIDO and avances
    assert [p.name for p in (tmp_path / "updates").iterdir()] == [ruta.name]


def test_borra_los_instaladores_antiguos_y_parciales(tmp_path):
    carpeta = tmp_path / "updates"
    carpeta.mkdir()
    (carpeta / "FT-Markdown-Setup-0.9.0.exe").write_bytes(b"viejo")
    (carpeta / "x.part").write_bytes(b"parcial")
    (carpeta / "sub").mkdir()
    (carpeta / "sub" / "y").write_bytes(b"1")
    servicio, release = _disponible(tmp_path, Fuente([_release("v1.0.0")]))
    servicio.download(release)
    assert [p.name for p in carpeta.iterdir()] == ["FT-Markdown-Setup-1.0.0.exe"]


def test_hash_distinto_es_error_de_integridad_y_no_deja_archivo(tmp_path):
    fuente = Fuente([_release("v1.0.0")], hash_texto="00" * 32)
    servicio, release = _disponible(tmp_path, fuente)
    with pytest.raises(UpdateError) as info:
        servicio.download(release)
    assert info.value.kind is UpdateErrorKind.INTEGRITY
    assert list((tmp_path / "updates").iterdir()) == []


@pytest.mark.parametrize("texto", ["no es un hash", "ab" * 32 + "  otro.exe"])
def test_archivo_sha256_ilegible_o_de_otro_instalador(tmp_path, texto):
    servicio, release = _disponible(tmp_path, Fuente([_release("v1.0.0")], hash_texto=texto))
    with pytest.raises(UpdateError) as info:
        servicio.download(release)
    assert info.value.kind is UpdateErrorKind.BAD_RESPONSE


def test_tamano_distinto_al_de_la_api_se_rechaza_y_no_deja_archivo(tmp_path):
    # La API anuncio un tamano y el servidor entrega otro.
    fuente = Fuente([_release("v1.0.0", tamano=len(CONTENIDO) + 7)])
    servicio, release = _disponible(tmp_path, fuente)
    with pytest.raises(UpdateError) as info:
        servicio.download(release)
    assert info.value.kind is UpdateErrorKind.SIZE_MISMATCH
    assert list((tmp_path / "updates").iterdir()) == []


def test_un_instalador_gigante_se_rechaza_sin_descargar(tmp_path):
    fuente = Fuente([_release("v1.0.0")])
    servicio, release = _disponible(tmp_path, fuente)
    gigante = replace(release, installer=replace(release.installer, size=MAX_INSTALLER_BYTES + 1))
    with pytest.raises(UpdateError) as info:
        servicio.download(gigante)
    assert info.value.kind is UpdateErrorKind.TOO_LARGE and fuente.descargas == 0


def test_descarga_cancelada_no_deja_nada(tmp_path):
    servicio, release = _disponible(tmp_path, Fuente([_release("v1.0.0")]))
    with pytest.raises(UpdateError) as info:
        servicio.download(release, cancelled=lambda: True)
    assert info.value.kind is UpdateErrorKind.CANCELLED
    assert list((tmp_path / "updates").iterdir()) == []


def test_carpeta_de_destino_inutilizable_es_error_de_disco(tmp_path):
    servicio, release = _disponible(tmp_path, Fuente([_release("v1.0.0")]))
    (tmp_path / "updates").write_text("soy un archivo")
    with pytest.raises(UpdateError) as info:
        servicio.download(release)
    assert info.value.kind is UpdateErrorKind.DISK
