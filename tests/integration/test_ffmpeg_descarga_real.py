"""Descarga REAL de ffmpeg (T015). Requiere internet: solo corre con `pytest -m network`.

Comprueba tambien que la URL fijada en `FFMPEG` sigue activa (T027 la repite antes de publicar).
"""

import subprocess

import pytest

from ft_markdown.adapters import audio_transcriber
from ft_markdown.adapters.ffmpeg_provider import FFMPEG, UrllibDownloader
from ft_markdown.app.components import ComponentManager

pytestmark = pytest.mark.network


def test_descarga_verifica_registra_y_convierte_un_mp3_a_wav(tmp_path):
    gestor = ComponentManager(tmp_path / "components", UrllibDownloader())
    exe = gestor.ensure(FFMPEG, confirm=lambda spec: True)  # el hash se verifica dentro

    version = subprocess.run([str(exe), "-version"], capture_output=True, text=True, check=True)
    assert "--enable-gpl" not in version.stdout
    assert "--enable-nonfree" not in version.stdout
    assert gestor.executable(FFMPEG) == exe

    mp3 = tmp_path / "tono.mp3"
    subprocess.run(
        [str(exe), "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1"]
        + ["-c:a", "libmp3lame", str(mp3)],
        check=True,
    )
    wav = audio_transcriber._to_wav(mp3, str(exe))
    assert wav.read(4) == b"RIFF"
