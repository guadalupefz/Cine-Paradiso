import mysql.connector
from flask import Blueprint, jsonify

from src.db import get_connection
from src.repositories.salas_repository import obtener_salas_por_local

salas_bp = Blueprint("salas", __name__)


@salas_bp.route("/locales/<int:id_local>/salas", methods=["GET"])
def listar_salas(id_local):
    if id_local <= 0:
        return jsonify({
            "error": "ID_LOCAL_INVALIDO",
            "mensaje": "El ID del local debe ser positivo."
        }), 400

    conn = None

    try:
        conn = get_connection()

        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT id_local FROM local WHERE id_local = %s",
                (id_local,)
            )

            if cursor.fetchone() is None:
                return jsonify({
                    "error": "LOCAL_NO_ENCONTRADO",
                    "mensaje": "No existe un local con ese ID."
                }), 404

            salas = obtener_salas_por_local(cursor, id_local)

        return jsonify({"salas": salas}), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudieron consultar las salas."
        }), 500

    except Exception:
        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "Ocurrió un error interno en el servidor."
        }), 500

    finally:
        if conn is not None:
            conn.close()
