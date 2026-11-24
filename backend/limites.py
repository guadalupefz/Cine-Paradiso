"""Control de intentos de login y registro por IP y ruta."""
import time
from math import ceil
from threading import Lock
from flask import current_app, jsonify, request

SEGUNDOS_HORA = 60 * 60
SEGUNDOS_DIA = 24 * SEGUNDOS_HORA
bloqueo_intentos = Lock()


def conservar_recientes(instantes, ahora, duracion):
    recientes = []
    for instante in instantes:
        if ahora - instante < duracion:
            recientes.append(instante)
    return recientes


def segundos_de_espera(instantes, ahora, duracion, maximo):
    if len(instantes) < maximo:
        return 0
    return ceil(duracion - (ahora - instantes[0]))


def registrar_intento(ahora, max_dia, max_hora):
    historiales = current_app.extensions.setdefault("limites_solicitudes", {})
    clave = (request.endpoint, request.remote_addr)
    dia = conservar_recientes(historiales.get(clave, []), ahora, SEGUNDOS_DIA)
    historiales[clave] = dia
    hora = conservar_recientes(dia, ahora, SEGUNDOS_HORA)
    espera_dia = segundos_de_espera(dia, ahora, SEGUNDOS_DIA, max_dia)
    espera_hora = segundos_de_espera(hora, ahora, SEGUNDOS_HORA, max_hora)
    espera = max(espera_dia, espera_hora)
    if espera == 0:
        dia.append(ahora)
    return espera


def controlar_intentos(max_dia=200, max_hora=50):
    with bloqueo_intentos:
        espera = registrar_intento(time.monotonic(), max_dia, max_hora)
    if espera:
        return (
            jsonify({"error": "Demasiados intentos. Intentá nuevamente más tarde."}),
            429,
            {"Retry-After": str(espera)},
        )
    return None
