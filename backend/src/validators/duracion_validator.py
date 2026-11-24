"""Compatibilidad entre minutos numericos y Runtime de OMDb."""
import re


def minutos_de_duracion(valor):
    if type(valor) is int:
        minutos = valor
    elif isinstance(valor, str):
        coincidencia = re.fullmatch(r"\s*(\d+)\s*(?:min)?\s*", valor, re.IGNORECASE)
        if not coincidencia:
            raise ValueError("La duración de la película no es válida.")
        minutos = int(coincidencia.group(1))
    else:
        raise ValueError("La duración de la película no es válida.")
    if not 1 <= minutos <= 1440:
        raise ValueError("La duración debe estar entre 1 y 1440 minutos.")
    return minutos
