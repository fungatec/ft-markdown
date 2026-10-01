"""Transcripcion de audio con idioma seleccionable (FR-010).

MarkItDown 0.1.8 transcribe siempre en ingles (`recognize_google` sin idioma) y no ofrece una
opcion para cambiarlo, asi que el audio se atiende aqui con las mismas bibliotecas que usa
MarkItDown (SpeechRecognition y pydub). El audio se envia al servicio gratuito Google Web Speech.
"""

from __future__ import annotations

import io
import shutil
from pathlib import Path

from ..core.errors import ConversionError, ErrorKind

COMPRESSED_SUFFIXES = frozenset({".mp3", ".m4a"})


def transcribe(path: Path, language: str, *, ffmpeg: str | None = None) -> str:
    """Devuelve el texto de la grabacion. Lanza ConversionError si no es posible.

    `ffmpeg` es la ruta del ejecutable (el gestor de componentes la dara en T015); si es None se
    busca en el PATH. Solo MP3 y M4A lo necesitan; WAV se lee directamente.
    """
    import speech_recognition as sr

    suffix = path.suffix.lower()
    try:
        if suffix in COMPRESSED_SUFFIXES:
            fuente = _to_wav(path, ffmpeg)
        else:
            fuente = str(path)
        reconocedor = sr.Recognizer()
        with sr.AudioFile(fuente) as audio_file:
            audio = reconocedor.record(audio_file)
        texto = reconocedor.recognize_google(audio, language=language)
    except ConversionError:
        raise
    except sr.UnknownValueError as exc:
        raise ConversionError(
            "Sin voz reconocible", kind=ErrorKind.EMPTY_RESULT, source=path
        ) from exc
    except sr.RequestError as exc:
        raise ConversionError(str(exc), kind=ErrorKind.NETWORK, source=path) from exc
    except FileNotFoundError as exc:
        raise ConversionError(str(exc), kind=ErrorKind.FILE_NOT_FOUND, source=path) from exc
    except Exception as exc:
        raise ConversionError(
            str(exc) or type(exc).__name__, kind=ErrorKind.CORRUPT_FILE, source=path
        ) from exc
    texto = texto.strip()
    if not texto:
        raise ConversionError("Sin voz reconocible", kind=ErrorKind.EMPTY_RESULT, source=path)
    return texto


def _to_wav(path: Path, ffmpeg: str | None) -> io.BytesIO:
    ejecutable = ffmpeg or shutil.which("ffmpeg")
    if not ejecutable:
        raise ConversionError(
            "ffmpeg no esta disponible", kind=ErrorKind.MISSING_COMPONENT, source=path
        )
    import os

    import pydub

    pydub.AudioSegment.converter = ejecutable
    # pydub localiza ffprobe solo en el PATH; el componente lo trae junto a ffmpeg.exe.
    carpeta = str(Path(ejecutable).parent)
    if carpeta not in os.environ.get("PATH", "").split(os.pathsep):
        os.environ["PATH"] = carpeta + os.pathsep + os.environ.get("PATH", "")
    salida = io.BytesIO()
    pydub.AudioSegment.from_file(path).export(salida, format="wav")
    salida.seek(0)
    return salida
