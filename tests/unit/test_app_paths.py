from pathlib import Path

from ft_markdown.adapters.app_paths import data_dir


def test_la_carpeta_de_datos_se_llama_ft_markdown_y_no_es_la_de_instalacion():
    carpeta = data_dir()
    assert carpeta.name == "FT Markdown"
    assert Path(__file__).resolve().parents[2] not in carpeta.parents


def test_los_componentes_van_en_local_appdata_y_no_en_la_carpeta_de_ajustes():
    from ft_markdown.adapters.app_paths import components_dir, local_data_dir

    local = local_data_dir()
    assert local.name == "FT Markdown"
    assert Path(__file__).resolve().parents[2] not in local.parents
    assert components_dir() == local / "components"


def test_updates_dir_esta_en_la_carpeta_local_y_no_en_la_de_datos():
    from ft_markdown.adapters.app_paths import data_dir, local_data_dir, updates_dir

    assert updates_dir() == local_data_dir() / "updates"
    assert data_dir() not in updates_dir().parents
