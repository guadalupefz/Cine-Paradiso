import mysql.connector
from flask import Blueprint, jsonify

from src.db import get_connection
from src.repositories.peliculas_locales_funciones import obtener_peliculas

peliculas_bp = Blueprint("peliculas", __name__)


@peliculas_bp.route("/peliculas", methods=["GET"])
def listar_peliculas():
    conn = None

    try:
        conn = get_connection()

        with conn.cursor(dictionary=True) as cursor:
            peliculas = obtener_peliculas(cursor)

        return jsonify({"peliculas": peliculas}), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudieron consultar las películas."
        }), 500

    except Exception:
        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "Ocurrió un error interno en el servidor."
        }), 500

    finally:
        if conn is not None:
            conn.close()
