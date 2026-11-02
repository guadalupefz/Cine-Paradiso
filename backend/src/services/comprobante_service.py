from backend.db.db import get_connection

from backend.src.repositories.compra_repository import (
    obtener_datos_comprobante,
    obtener_entradas_comprobante,
    obtener_servicios_de_compra
)


def obtener_comprobante(id_compra, id_usuario):
    conn = get_connection()

    try:
        with conn.cursor(dictionary=True) as cursor:

            compra = obtener_datos_comprobante(
                cursor, id_compra, id_usuario
            )

            if compra is None:
                return None

            entradas = obtener_entradas_comprobante(
                cursor, id_compra
            )

            servicios = obtener_servicios_de_compra(
                cursor, id_compra
            )

            return {
                "compra": compra,
                "entradas": entradas,
                "servicios": servicios
            }

    finally:
        conn.close()