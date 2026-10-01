import json

from ft_markdown.adapters.json_settings import JsonSettingsStore
from ft_markdown.core.settings import Settings


def test_sin_archivo_devuelve_los_valores_por_defecto(tmp_path):
    ajustes = JsonSettingsStore(tmp_path / "settings.json").load()
    assert ajustes == Settings()
    assert ajustes.theme == "dark" and ajustes.check_updates is True
    assert ajustes.audio_language == "es-MX" and ajustes.output_dir is None


def test_guardar_y_cargar_conserva_los_valores_con_acentos_y_espacios(tmp_path):
    tienda = JsonSettingsStore(tmp_path / "settings.json")
    ajustes = Settings(output_dir="C:\\Users\\Ñandú\\Mis documentos", theme="light")
    tienda.save(ajustes)
    assert tienda.load() == ajustes


def test_crea_la_carpeta_si_no_existe(tmp_path):
    destino = tmp_path / "FT Markdown" / "settings.json"
    JsonSettingsStore(destino).save(Settings())
    assert destino.exists()


def test_el_archivo_es_utf8_legible(tmp_path):
    destino = tmp_path / "settings.json"
    JsonSettingsStore(destino).save(Settings(output_dir="Año"))
    assert json.loads(destino.read_text(encoding="utf-8"))["output_dir"] == "Año"


def test_archivo_corrupto_devuelve_defaults_y_conserva_copia(tmp_path):
    destino = tmp_path / "settings.json"
    destino.write_text("{ esto no es json", encoding="utf-8")
    assert JsonSettingsStore(destino).load() == Settings()
    assert (tmp_path / "settings.json.bak").read_text(encoding="utf-8") == "{ esto no es json"


def test_claves_desconocidas_se_ignoran_y_valores_invalidos_vuelven_al_defecto(tmp_path):
    destino = tmp_path / "settings.json"
    destino.write_text(
        json.dumps({"theme": "morado", "check_updates": "si", "futuro": 1, "output_dir": "X"}),
        encoding="utf-8",
    )
    ajustes = JsonSettingsStore(destino).load()
    assert ajustes.theme == "dark"
    assert ajustes.check_updates is True
    assert ajustes.output_dir == "X"


def test_la_escritura_no_deja_archivos_temporales(tmp_path):
    JsonSettingsStore(tmp_path / "settings.json").save(Settings())
    assert [p.name for p in tmp_path.iterdir()] == ["settings.json"]
