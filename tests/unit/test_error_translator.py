from pathlib import Path

import pytest

from ft_markdown.core.errors import ConversionError, ErrorKind, ErrorTranslator

traductor = ErrorTranslator()


@pytest.mark.parametrize("tipo", list(ErrorKind))
def test_cada_tipo_de_error_tiene_mensaje_completo_en_espanol(tipo: ErrorKind):
    mensaje = traductor.translate(ConversionError("technical detail", kind=tipo))
    assert mensaje.title and mensaje.cause and mensaje.suggestion
    assert "technical detail" not in mensaje.title + mensaje.cause + mensaje.suggestion
    assert mensaje.detail == "technical detail"


def test_pdf_sin_texto_tiene_regla_propia():
    error = ConversionError("", kind=ErrorKind.EMPTY_RESULT, source=Path("escaneo.PDF"))
    mensaje = traductor.translate(error)
    assert mensaje.title == "PDF sin texto"
    assert "escaneo" in mensaje.cause.lower()
    assert "OCR" in mensaje.suggestion


def test_resultado_vacio_en_otro_formato_usa_mensaje_generico():
    mensaje = traductor.translate(
        ConversionError("", kind=ErrorKind.EMPTY_RESULT, source=Path("nota.docx"))
    )
    assert mensaje.title != "PDF sin texto"
    assert "sin contenido" in mensaje.title.lower()


def test_imagen_sin_texto_explica_que_la_descripcion_llega_despues():
    mensaje = traductor.translate(
        ConversionError("", kind=ErrorKind.EMPTY_RESULT, source=Path("foto.png"))
    )
    assert "imagen" in mensaje.title.lower()


def test_error_de_red_aclara_que_los_archivos_locales_siguen_funcionando():
    mensaje = traductor.translate(ConversionError("x", kind=ErrorKind.NETWORK))
    assert "conexi" in mensaje.title.lower()
    assert "locales" in mensaje.suggestion.lower()


def test_una_excepcion_ajena_se_traduce_como_error_desconocido():
    mensaje = traductor.translate(RuntimeError("boom"))
    assert mensaje.title and mensaje.detail == "boom"


def test_un_conversion_error_sin_tipo_es_desconocido():
    assert ConversionError("x").kind is ErrorKind.UNKNOWN


def test_el_texto_completo_junta_titulo_causa_y_sugerencia():
    mensaje = traductor.translate(ConversionError("x", kind=ErrorKind.NETWORK))
    assert mensaje.title in mensaje.text and mensaje.suggestion in mensaje.text
