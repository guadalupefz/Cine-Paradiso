import logging

from flask import Blueprint, jsonify, request
from mysql.connector import Error as MySQLError

from backend.db.db import get_connection
from backend.seguridad import admin_required
from backend.src.repositories.peliculas_repository import guardar_pelicula
from backend.src.services.omdb_service import (
    obtener_pelicula_por_titulo,
    preparar_pelicula_para_guardar,
)


peliculas_bp = Blueprint("peliculas_externas", __name__)
logger = logging.getLogger(__name__)


def _respuesta_error_omdb(error):
    if isinstance(error, TimeoutError):
        estado = 504
    elif isinstance(error, ValueError):
        estado = 404
    else:
        estado = 502
    return jsonify({"error": str(error)}), estado


@peliculas_bp.route("/pelicula", methods=["GET", "POST"])
@admin_required
def consultar_pelicula(id_usuario):
    titulo = request.args.get("titulo")
    if not isinstance(titulo, str) or not titulo.strip():
        return jsonify({"error": "El título de búsqueda es obligatorio."}), 400

    try:
        datos = obtener_pelicula_por_titulo(titulo.strip())
    except (ConnectionError, RuntimeError, TimeoutError, ValueError) as error:
        return _respuesta_error_omdb(error)

    if request.method == "GET":
        return jsonify(datos), 200

    try:
        pelicula = preparar_pelicula_para_guardar(datos)
    except (KeyError, TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 422

    conexion = None
    cursor = None
    try:
        conexion = get_connection()
        cursor = conexion.cursor(dictionary=True, buffered=True)
        resultado = guardar_pelicula(cursor, pelicula)
        if not resultado["exito"]:
            conexion.rollback()
            return jsonify({"error": resultado["error"]}), 422

        conexion.commit()
        if resultado["accion"] == "actualizada":
            return jsonify({
                "mensaje": "Película actualizada correctamente.",
                "accion": "actualizada",
            }), 200
        return jsonify(datos), 201
    except MySQLError:
        if conexion is not None:
            conexion.rollback()
        logger.exception("No se pudo guardar la película de OMDb.")
        return jsonify({"error": "No se pudo guardar la película."}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()
