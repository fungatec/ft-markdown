from pathlib import Path

import pytest

from ft_markdown.core.errors import ConversionError, ErrorKind
from ft_markdown.core.models import ConversionJob, ConversionResult, JobState

ORIGEN = Path("informe.pdf")


def _resultado() -> ConversionResult:
    return ConversionResult(source=ORIGEN, markdown="# Hola")


def test_un_trabajo_nuevo_esta_pendiente_y_sin_resultado():
    trabajo = ConversionJob(source=ORIGEN)
    assert trabajo.state is JobState.PENDING
    assert trabajo.result is None and trabajo.error is None
    assert not trabajo.is_finished


def test_flujo_normal_hasta_listo():
    trabajo = ConversionJob(source=ORIGEN).start()
    assert trabajo.state is JobState.CONVERTING
    final = trabajo.finish(_resultado())
    assert final.state is JobState.DONE and final.result == _resultado()
    assert final.is_finished


def test_flujo_con_error_conserva_el_error():
    error = ConversionError("falla", kind=ErrorKind.CORRUPT_FILE, source=ORIGEN)
    final = ConversionJob(source=ORIGEN).start().fail(error)
    assert final.state is JobState.ERROR and final.error is error


def test_se_puede_cancelar_pendiente_o_en_curso():
    assert ConversionJob(source=ORIGEN).cancel().state is JobState.CANCELLED
    assert ConversionJob(source=ORIGEN).start().cancel().state is JobState.CANCELLED


def test_los_trabajos_son_inmutables():
    trabajo = ConversionJob(source=ORIGEN)
    trabajo.start()
    assert trabajo.state is JobState.PENDING


@pytest.mark.parametrize(
    "transicion",
    [
        lambda j: j.finish(_resultado()),  # pendiente -> listo
        lambda j: j.fail(ConversionError("x")),  # pendiente -> error
        lambda j: j.start().finish(_resultado()).start(),  # listo -> convirtiendo
        lambda j: j.start().finish(_resultado()).cancel(),  # listo -> cancelado
        lambda j: j.cancel().start(),  # cancelado -> convirtiendo
    ],
)
def test_transiciones_invalidas_lanzan_valueerror(transicion):
    with pytest.raises(ValueError):
        transicion(ConversionJob(source=ORIGEN))
