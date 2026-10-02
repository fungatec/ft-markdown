"""Consulta REAL a la API de GitHub (T016). Requiere internet: solo con `pytest -m network`."""

import pytest

from ft_markdown.adapters.github_releases import GitHubReleases
from ft_markdown.core.updates import UpdateError, UpdateErrorKind

pytestmark = pytest.mark.network


def test_la_api_publica_responde_con_una_lista():
    try:
        releases = GitHubReleases().list_releases()
    except UpdateError as error:
        # Un limite de uso es una respuesta valida del servidor; cualquier otra cosa es un fallo.
        assert error.kind is UpdateErrorKind.RATE_LIMIT
        return
    assert isinstance(releases, list)
