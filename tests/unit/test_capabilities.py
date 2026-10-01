from pathlib import Path

import pytest

from ft_markdown.core.capabilities import (
    CATALOG,
    InputKind,
    Reason,
    availability,
    find_for_path,
    get,
)

# Formatos locales de la tabla 3 de la especificacion (FR-002): deben resolverse sin red.
LOCALES = [
    ".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".html", ".htm", ".csv", ".json", ".xml",
    ".txt", ".ipynb", ".epub", ".msg", ".zip", ".jpg", ".jpeg", ".png",
]  # fmt: skip


def test_identificadores_unicos():
    ids = [c.id for c in CATALOG]
    assert len(ids) == len(set(ids))


def test_extensiones_en_minuscula_con_punto_y_sin_repetir():
    todas = [e for c in CATALOG for e in c.extensions]
    assert all(e.startswith(".") and e == e.lower() for e in todas)
    assert len(todas) == len(set(todas))


@pytest.mark.parametrize("extension", LOCALES)
def test_formatos_locales_se_convierten_sin_red(extension: str):
    capacidad = find_for_path(Path(f"documento{extension}"))
    assert capacidad is not None
    assert not capacidad.requires_network
    assert availability(capacidad, online=False).enabled


def test_busqueda_ignora_mayusculas_y_extension_desconocida():
    assert find_for_path(Path("INFORME.PDF")) is get("pdf")
    assert find_for_path(Path("programa.exe")) is None
    assert find_for_path(Path("sin_extension")) is None


def test_sin_conexion_se_desactivan_las_funciones_en_linea():
    for id_ in ("url", "youtube", "audio-wav"):
        estado = availability(get(id_), online=False)
        assert not estado.enabled
        assert estado.reason is Reason.OFFLINE
        assert availability(get(id_), online=True).enabled


def test_url_y_youtube_son_entradas_de_enlace_sin_extensiones():
    for id_ in ("url", "youtube"):
        capacidad = get(id_)
        assert capacidad.input_kind is InputKind.URL
        assert capacidad.extensions == ()


def test_mp3_y_m4a_requieren_ffmpeg_pero_wav_no():
    for extension in (".mp3", ".m4a"):
        capacidad = find_for_path(Path(f"nota{extension}"))
        assert capacidad is not None and capacidad.component == "ffmpeg"
        sin = availability(capacidad, online=True)
        assert not sin.enabled and sin.reason is Reason.MISSING_COMPONENT
        assert availability(capacidad, online=True, components=frozenset({"ffmpeg"})).enabled
    assert get("audio-wav").component is None


def test_funciones_de_fase_2_no_estan_disponibles_en_la_v1():
    fase2 = [c for c in CATALOG if c.phase == 2]
    assert {c.id for c in fase2} >= {"llm-descripcion", "ocr", "azure"}
    for capacidad in fase2:
        assert capacidad.requires_network and capacidad.requires_credentials
        estado = availability(
            capacidad, online=True, components=frozenset({"ffmpeg"}), credentials=frozenset({"x"})
        )
        assert not estado.enabled and estado.reason is Reason.NOT_IN_VERSION


def test_capacidad_inexistente_lanza_keyerror():
    with pytest.raises(KeyError):
        get("no-existe")
