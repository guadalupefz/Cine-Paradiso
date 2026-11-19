from flask_jwt_extended import jwt_required
import logging
import os

from flask import Blueprint, jsonify, request
from mysql.connector import Error as MySQLError, IntegrityError

from backend.db.db import get_connection
from backend.seguridad import verificar_acceso
from backend.src.services.omdb_service import (
    buscar_peliculas,
    obtener_pelicula_por_id,
    obtener_pelicula_por_titulo,
    preparar_pelicula_para_guardar,
)
from backend.src.services.peliculas_service import (
    listar_peliculas_service,
    crear_pelicula_service,
    editar_pelicula_service,
    importar_pelicula_service,
)
from backend.src.validators.omdb_validator import (
    validar_busqueda_omdb,
    validar_detalle_omdb,
    validar_importacion_omdb,
)
from backend.src.validators.peliculas_validator import (
    validar_id_pelicula,
    validar_pelicula,
)


peliculas_bp = Blueprint("peliculas", __name__)
logger = logging.getLogger(__name__)


def _respuesta_error_omdb(error):
    if not os.getenv("OMDB_API_KEY", "").strip():
        estado = 503
    elif isinstance(error, TimeoutError):
        estado = 504
    elif isinstance(error, ValueError):
        estado = 404
    else:
        estado = 502
    return jsonify({"error": str(error)}), estado


def _persistir_pelicula_omdb(datos_omdb):
    try:
        pelicula = preparar_pelicula_para_guardar(datos_omdb)
    except (KeyError, TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 422

    conexion = None
    cursor = None
    try:
        conexion = get_connection()
        cursor = conexion.cursor(dictionary=True, buffered=True)
        resultado = importar_pelicula_service(cursor, pelicula)
        if not resultado["exito"]:
            conexion.rollback()
            return jsonify({"error": resultado["error"]}), resultado.get("status", 422)

        conexion.commit()
        mensaje = (
            "Película actualizada correctamente."
            if resultado["accion"] == "actualizada"
            else "Película importada correctamente."
        )
        return jsonify({
            "mensaje": mensaje,
            "id_pelicula": resultado["id"],
            "id_externo_api": pelicula["id_externo_api"],
            "titulo": pelicula["titulo"],
            "accion": resultado["accion"],
        }), 200 if resultado["accion"] == "actualizada" else 201
    except IntegrityError:
        if conexion is not None:
            conexion.rollback()
        return jsonify({"error": "La película entra en conflicto con un registro existente."}), 409
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


@peliculas_bp.route("/peliculas", methods=["GET"])
def listar_peliculas():
    conexion = None
    cursor = None
    try:
        conexion = get_connection()
        cursor = conexion.cursor(dictionary=True, buffered=True)
        resultado = listar_peliculas_service(cursor)
        return jsonify(resultado["data"]), resultado["status"]
    except MySQLError:
        logger.exception("No se pudieron consultar las películas.")
        return jsonify({"error": "No se pudieron cargar las películas."}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()


@peliculas_bp.route("/pelicula", methods=["GET", "POST"])
@jwt_required()
def consultar_pelicula():
    id_usuario, respuesta_acceso = verificar_acceso(('administrador',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    titulo = request.args.get("titulo")
    error = validar_busqueda_omdb(titulo)
    if error:
        return jsonify({"error": error}), 400

    try:
        datos = obtener_pelicula_por_titulo(titulo.strip())
    except (ConnectionError, RuntimeError, TimeoutError, ValueError) as error:
        return _respuesta_error_omdb(error)

    if request.method == "GET":
        return jsonify(datos), 200

    return _persistir_pelicula_omdb(datos)


@peliculas_bp.route("/peliculas", methods=["POST"])
@jwt_required()
def crear_pelicula_manual():
    id_usuario, respuesta_acceso = verificar_acceso(('administrador',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    datos_validados, error = validar_pelicula(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400

    conexion = None
    cursor = None
    try:
        conexion = get_connection()
        cursor = conexion.cursor(dictionary=True, buffered=True)
        resultado = crear_pelicula_service(cursor, datos_validados)
        if resultado["status"] < 400:
            conexion.commit()
        else:
            conexion.rollback()
        return jsonify(resultado["data"]), resultado["status"]
    except MySQLError:
        if conexion is not None:
            conexion.rollback()
        logger.exception("No se pudo guardar la película.")
        return jsonify({"error": "No se pudo guardar la película."}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()


@peliculas_bp.route("/peliculas/<int:id_pelicula>", methods=["PUT"])
@jwt_required()
def editar_pelicula_manual(id_pelicula):
    id_usuario, respuesta_acceso = verificar_acceso(('administrador',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    error_id = validar_id_pelicula(id_pelicula)
    if error_id:
        return jsonify({"error": error_id}), 400

    datos_validados, error = validar_pelicula(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400

    conexion = None
    cursor = None
    try:
        conexion = get_connection()
        cursor = conexion.cursor(dictionary=True, buffered=True)
        resultado = editar_pelicula_service(
            cursor,
            id_pelicula,
            datos_validados,
        )
        if resultado["status"] < 400:
            conexion.commit()
        else:
            conexion.rollback()
        return jsonify(resultado["data"]), resultado["status"]
    except MySQLError:
        if conexion is not None:
            conexion.rollback()
        logger.exception("No se pudo actualizar la película.")
        return jsonify({"error": "No se pudo actualizar la película."}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()


@peliculas_bp.route("/peliculas/omdb/buscar", methods=["GET"])
@jwt_required()
def buscar_peliculas_omdb():
    id_usuario, respuesta_acceso = verificar_acceso(('administrador',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    titulo = request.args.get("titulo")
    if not isinstance(titulo, str):
        return jsonify({"error": "El título de búsqueda es obligatorio."}), 400

    error = validar_busqueda_omdb(titulo)
    if error:
        return jsonify({"error": error}), 400

    try:
        return jsonify(buscar_peliculas(titulo.strip())), 200
    except (ConnectionError, RuntimeError, TimeoutError, ValueError) as error:
        return _respuesta_error_omdb(error)


@peliculas_bp.route("/peliculas/omdb/detalle", methods=["GET"])
@jwt_required()
def obtener_detalle_omdb():
    id_usuario, respuesta_acceso = verificar_acceso(('administrador',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    imdb_id = request.args.get("imdb_id")
    if not isinstance(imdb_id, str):
        return jsonify({"error": "El IMDb ID es obligatorio."}), 400

    error = validar_detalle_omdb(imdb_id)
    if error:
        return jsonify({"error": error}), 400

    try:
        return jsonify(obtener_pelicula_por_id(imdb_id.strip())), 200
    except (ConnectionError, RuntimeError, TimeoutError, ValueError) as error:
        return _respuesta_error_omdb(error)


@peliculas_bp.route("/peliculas/omdb/importar", methods=["POST"])
@jwt_required()
def importar_pelicula_omdb():
    id_usuario, respuesta_acceso = verificar_acceso(('administrador',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "Se esperaba un objeto JSON."}), 400

    error = validar_importacion_omdb(datos)
    if error:
        return jsonify({"error": error}), 400

    imdb_id = datos.get("imdb_id")
    if not isinstance(imdb_id, str):
        return jsonify({"error": "El IMDb ID es obligatorio."}), 400

    try:
        pelicula = obtener_pelicula_por_id(imdb_id)
    except (ConnectionError, RuntimeError, TimeoutError, ValueError) as error:
        return _respuesta_error_omdb(error)

    return _persistir_pelicula_omdb(pelicula)
