from datetime import datetime


def validar_inicio_funcion(fecha_inicio, ahora):
    if not isinstance(fecha_inicio, datetime) or not isinstance(ahora, datetime):
        raise ValueError("No se pudo validar el horario de la función.")
    if fecha_inicio <= ahora:
        raise ValueError("La función ya comenzó. No se pueden realizar compras ni reservas.")
