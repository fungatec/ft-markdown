"""Errores del nucleo. El traductor a mensajes en espanol llega en la tarea T010."""


class ConversionError(Exception):
    """No se pudo convertir un documento. El mensaje describe la causa."""
