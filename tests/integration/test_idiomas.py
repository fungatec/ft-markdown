"""T011: las preferencias de idioma llegan a MarkItDown y al transcriptor (FR-009, FR-010)."""

import struct
import wave
from pathlib import Path

import pytest

pytest.importorskip("markitdown")
sr = pytest.importorskip("speech_recognition")

from ft_markdown.adapters import audio_transcriber  # noqa: E402
from ft_markdown.adapters.markitdown_engine import MarkItDownEngine  # noqa: E402
from ft_markdown.core.errors import ConversionError, ErrorKind  # noqa: E402
from ft_markdown.core.models import ConversionOptions  # noqa: E402


def _wav_silencioso(ruta: Path) -> Path:
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(struct.pack("<h", 0) * 1600)
    return ruta


def test_opciones_por_defecto_son_espanol():
    opciones = ConversionOptions()
    assert opciones.audio_language == "es-MX"
    assert opciones.youtube_languages == ("es", "en")


def test_el_audio_se_transcribe_en_es_mx_por_defecto(tmp_path, monkeypatch):
    idiomas = []

    def falso(self, audio, language="en-US", **kwargs):
        idiomas.append(language)
        return "hola mundo"

    monkeypatch.setattr(sr.Recognizer, "recognize_google", falso)
    resultado = MarkItDownEngine().convert_file(_wav_silencioso(tmp_path / "nota.wav"))

    assert idiomas == ["es-MX"]
    assert "hola mundo" in resultado.markdown


def test_el_idioma_del_audio_es_configurable(tmp_path, monkeypatch):
    idiomas = []
    monkeypatch.setattr(
        sr.Recognizer,
        "recognize_google",
        lambda self, a, language="en-US": idiomas.append(language) or "ok",
    )
    motor = MarkItDownEngine(ConversionOptions(audio_language="en-US"))
    motor.convert_file(_wav_silencioso(tmp_path / "nota.wav"))
    assert idiomas == ["en-US"]


def test_audio_sin_voz_es_resultado_vacio(tmp_path, monkeypatch):
    def sin_voz(self, audio, language="en-US"):
        raise sr.UnknownValueError()

    monkeypatch.setattr(sr.Recognizer, "recognize_google", sin_voz)
    with pytest.raises(ConversionError) as info:
        MarkItDownEngine().convert_file(_wav_silencioso(tmp_path / "silencio.wav"))
    assert info.value.kind is ErrorKind.EMPTY_RESULT


def test_servicio_de_voz_inaccesible_es_error_de_red(tmp_path, monkeypatch):
    def caido(self, audio, language="en-US"):
        raise sr.RequestError("sin conexion")

    monkeypatch.setattr(sr.Recognizer, "recognize_google", caido)
    with pytest.raises(ConversionError) as info:
        MarkItDownEngine().convert_file(_wav_silencioso(tmp_path / "nota.wav"))
    assert info.value.kind is ErrorKind.NETWORK


def test_mp3_sin_ffmpeg_pide_el_componente(tmp_path, monkeypatch):
    monkeypatch.setattr(audio_transcriber.shutil, "which", lambda nombre: None)
    mp3 = tmp_path / "nota.mp3"
    mp3.write_bytes(b"ID3")
    with pytest.raises(ConversionError) as info:
        audio_transcriber.transcribe(mp3, "es-MX")
    assert info.value.kind is ErrorKind.MISSING_COMPONENT


def test_las_urls_piden_subtitulos_primero_en_espanol(monkeypatch):
    recibido = {}

    class Resultado:
        markdown = "# Video"
        title = "Video"

    def falso(url, **kwargs):
        recibido.update(url=url, **kwargs)
        return Resultado()

    motor = MarkItDownEngine()
    monkeypatch.setattr(motor._markitdown, "convert_url", falso)
    resultado = motor.convert_url("https://www.youtube.com/watch?v=abc")

    assert recibido["youtube_transcript_languages"] == ["es", "en"]
    assert resultado.source == "https://www.youtube.com/watch?v=abc"


def test_url_sin_conexion_se_clasifica_como_red(monkeypatch):
    from requests.exceptions import ConnectionError as SinRed

    def caido(url, **kwargs):
        raise SinRed("sin red")

    motor = MarkItDownEngine()
    monkeypatch.setattr(motor._markitdown, "convert_url", caido)
    with pytest.raises(ConversionError) as info:
        motor.convert_url("https://ejemplo.org")
    assert info.value.kind is ErrorKind.NETWORK
