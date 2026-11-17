import mysql.connector

from backend.db.db import get_connection
from backend.src.repositories.butacas_repository import (
    contar_butacas_de_sala,
    crear_butacas,
)
from backend.src.repositories.salas_repository import bloquear_sala


def configurar_butacas_servicio(id_sala, butacas):
    conn = None

    try:
        conn = get_connection()
        conn.start_transaction()

        with conn.cursor(dictionary=True) as cursor:
            sala = bloquear_sala(cursor, id_sala)

            if sala is None:
                conn.rollback()
                return {"error": "No existe la sala indicada."}, 404

            capacidad = sala["capacidad"]

            if len(butacas) != capacidad:
                conn.rollback()
                return {
                    "error": "La cantidad de butacas debe coincidir con la capacidad de la sala.",
                    "capacidad": capacidad,
                    "cantidad_butacas": len(butacas)
                }, 400

            if contar_butacas_de_sala(cursor, id_sala) > 0:
                conn.rollback()
                return {"error": "La sala ya tiene butacas configuradas."}, 409

            crear_butacas(cursor, id_sala, butacas)

        conn.commit()

        return {
            "mensaje": "Butacas configuradas correctamente.",
            "id_sala": id_sala,
            "cantidad": len(butacas)
        }, 201

    except mysql.connector.Error:
        if conn is not None:
            conn.rollback()
        return {"error": "No se pudieron configurar las butacas."}, 500

    finally:
        if conn is not None:
            conn.close()
