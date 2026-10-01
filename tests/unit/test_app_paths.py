from pathlib import Path

from ft_markdown.adapters.app_paths import data_dir


def test_la_carpeta_de_datos_se_llama_ft_markdown_y_no_es_la_de_instalacion():
    carpeta = data_dir()
    assert carpeta.name == "FT Markdown"
    assert Path(__file__).resolve().parents[2] not in carpeta.parents
