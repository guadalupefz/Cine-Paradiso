import mysql.connector
from flask import Blueprint, jsonify

from src.db import get_connection
from src.repositories.butacas_repository import obtener_butacas_por_funcion

mis_rutas = Blueprint('butacas', __name__)


@mis_rutas.route('/funciones/<int:id_funcion>/butacas', methods=['GET'])
def consultar_butacas(id_funcion):
    if id_funcion <= 0:
        return jsonify({
            "error": "ID_FUNCION_INVALIDO",
            "mensaje": "El ID de la función debe ser positivo."
        }), 400

    conn = None

    try:
        conn = get_connection()

        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT id_funcion FROM funcion WHERE id_funcion = %s",
                (id_funcion,)
            )

            if cursor.fetchone() is None:
                return jsonify({
                    "error": "FUNCION_NO_ENCONTRADA",
                    "mensaje": "No existe una función con ese ID."
                }), 404

            butacas = obtener_butacas_por_funcion(cursor, id_funcion)

        return jsonify({
            "id_funcion": id_funcion,
            "butacas": butacas
        }), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudieron consultar las butacas."
        }), 500

    except Exception:
        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "Ocurrió un error interno en el servidor."
        }), 500

    finally:
        if conn is not None:
            conn.close()
