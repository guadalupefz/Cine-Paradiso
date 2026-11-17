import mysql.connector

from backend.db.db import get_connection
from backend.src.constants import (
    ESTADO_COMPRA_CANCELADA,
    ESTADO_COMPRA_CONFIRMADA,
)
from backend.src.repositories import compra_repository as repo


ESTADOS_CANCELABLES = (
    ESTADO_COMPRA_CONFIRMADA,
    "aprobada",
)


def cancelar_compra(id_usuario, id_compra):
    conexion = None

    try:
        conexion = get_connection()
        conexion.start_transaction()

        with conexion.cursor(dictionary=True) as cursor:
            compra = repo.obtener_compra_para_cancelar(
                cursor, id_compra, id_usuario
            )

            if compra is None:
                conexion.rollback()
                return {"error": "Compra no encontrada"}, 404

            if compra["estado"] not in ESTADOS_CANCELABLES:
                conexion.rollback()
                return {
                    "error": "La compra no se puede cancelar en su estado actual"
                }, 409

            entradas = repo.obtener_entradas_para_cancelar(
                cursor, id_compra
            )

            if not entradas:
                conexion.rollback()
                return {"error": "La compra no tiene entradas"}, 409

            entradas_utilizadas = any(
                entrada["fecha_hora_validacion"] is not None
                for entrada in entradas
            )

            if entradas_utilizadas:
                conexion.rollback()
                return {"error": "La compra tiene entradas utilizadas"}, 409

            fuera_de_plazo = any(
                entrada["fuera_de_plazo"]
                for entrada in entradas
            )

            if fuera_de_plazo:
                conexion.rollback()
                return {
                    "error": "No se puede cancelar dentro de las dos horas previas a la función"
                }, 409

            repo.actualizar_estado_compra(
                cursor,
                id_compra,
                ESTADO_COMPRA_CANCELADA,
                compra["estado"]
            )

            repo.liberar_entradas_compra(cursor, id_compra)

        conexion.commit()

        return {
            "id_compra": id_compra,
            "estado": ESTADO_COMPRA_CANCELADA,
            "mensaje": "Compra cancelada correctamente"
        }, 200

    except Exception:
        if conexion is not None:
            conexion.rollback()
        raise

    finally:
        if conexion is not None:
            conexion.close()
