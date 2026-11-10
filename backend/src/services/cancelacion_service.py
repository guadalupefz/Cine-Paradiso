from backend.db.db import get_connection
from backend.src.constants import (
    ESTADO_COMPRA_CANCELADA,
    ESTADO_COMPRA_CONFIRMADA,
)


def cancelar_compra(id_usuario, id_compra):
    conexion = get_connection()

    try:
        conexion.start_transaction()

        with conexion.cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT estado
                FROM compra
                WHERE id_compra = %s AND id_usuario = %s
                FOR UPDATE
                """,
                (id_compra, id_usuario)
            )

            compra = cursor.fetchone()

            if compra is None:
                conexion.rollback()
                return {"error": "Compra no encontrada"}, 404

            if compra["estado"] != ESTADO_COMPRA_CONFIRMADA:
                conexion.rollback()
                return {
                    "error": "La compra no se puede cancelar en su estado actual"
                }, 409

            cursor.execute(
                """
                SELECT
                    entrada.fecha_hora_validacion,
                    funcion.fecha_hora_inicio <= DATE_ADD(
                        NOW(), INTERVAL 2 HOUR
                    ) AS fuera_de_plazo
                FROM entrada
                JOIN funcion ON entrada.id_funcion = funcion.id_funcion
                WHERE entrada.id_compra = %s
                FOR UPDATE
                """,
                (id_compra,)
            )

            entradas = cursor.fetchall()

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

            cursor.execute(
                """
                UPDATE compra
                SET estado = %s
                WHERE id_compra = %s
                """,
                (ESTADO_COMPRA_CANCELADA, id_compra)
            )

            cursor.execute(
                """
                UPDATE entrada
                SET ocupacion_activa = NULL
                WHERE id_compra = %s
                """,
                (id_compra,)
            )

        conexion.commit()

        return {
            "id_compra": id_compra,
            "estado": ESTADO_COMPRA_CANCELADA,
            "mensaje": "Compra cancelada correctamente"
        }, 200

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()
