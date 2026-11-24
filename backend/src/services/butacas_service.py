from backend.src.repositories.butacas_repository import (
    contar_butacas_de_sala,
    crear_butacas,
)
from backend.src.repositories.salas_repository import bloquear_sala


def configurar_butacas_servicio(cursor, id_sala, butacas):
    sala = bloquear_sala(cursor, id_sala)

    if sala is None:
        return None, "SALA_INEXISTENTE"

    capacidad = sala["capacidad"]

    if len(butacas) != capacidad:
        return {
            "capacidad": capacidad,
            "cantidad_butacas": len(butacas)
        }, "CAPACIDAD_INVALIDA"

    if contar_butacas_de_sala(cursor, id_sala) > 0:
        return None, "BUTACAS_YA_CONFIGURADAS"

    crear_butacas(cursor, id_sala, butacas)

    return {
        "mensaje": "Butacas configuradas correctamente.",
        "id_sala": id_sala,
        "cantidad": len(butacas)
    }, None
