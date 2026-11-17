from backend.src.repositories.compra_repository import (
    obtener_datos_comprobante,
    obtener_entradas_comprobante,
    obtener_servicios_de_compra
)

from backend.src.constants import ESTADO_COMPRA_CONFIRMADA


def obtener_comprobante(cursor, id_compra, id_usuario):
    compra = obtener_datos_comprobante(
        cursor, id_compra, id_usuario
    )

    if compra is None:
        return None

    solo_activas = compra["estado"] == ESTADO_COMPRA_CONFIRMADA

    entradas = obtener_entradas_comprobante(
        cursor,
        id_compra,
        solo_activas=solo_activas
    )

    servicios = obtener_servicios_de_compra(
        cursor, id_compra
    )

    return {
        "compra": compra,
        "entradas": entradas,
        "servicios": servicios
    }
