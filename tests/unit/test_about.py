import re

from ft_markdown import __main__ as entrada
from ft_markdown.__about__ import APP_NAME, __version__


def test_version_sigue_versionado_semantico():
    assert re.fullmatch(r"\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?", __version__)


def test_nombre_de_la_aplicacion():
    assert APP_NAME == "FT Markdown"


def test_version_por_linea_de_comandos(capsys):
    assert entrada.main(["--version"]) == 0
    assert capsys.readouterr().out.strip() == f"{APP_NAME} {__version__}"
