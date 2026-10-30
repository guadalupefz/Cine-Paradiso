import mysql.connector
from flask import Blueprint, jsonify

from src.db import get_connection
from src.repositories.peliculas_locales_funciones import obtener_locales

locales_bp = Blueprint("locales", __name__)


@locales_bp.route("/locales", methods=["GET"])
def listar_locales():
    conn = None

    try:
        conn = get_connection()

        with conn.cursor(dictionary=True) as cursor:
            locales = obtener_locales(cursor)

        return jsonify({"locales": locales}), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudieron consultar los locales."
        }), 500

    except Exception:
        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "Ocurrió un error interno en el servidor."
        }), 500

    finally:
        if conn is not None:
            conn.close()
