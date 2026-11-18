import logging

from flask import Blueprint, jsonify, request
from mysql.connector import Error as MySQLError

from db.db import get_connection
from backend.seguridad import admin_required

from backend.src.repositories.peliculas_repository import guardar_pelicula

from backend.src.services.peliculas_service import (
    listar_peliculas_service,
    crear_pelicula_service,
    editar_pelicula_service,
)

from backend.src.services.omdb_service import (
    buscar_peliculas,
    obtener_pelicula_por_id,
    preparar_pelicula_para_guardar,
)

from backend.src.validators.peliculas_validators import validar_pelicula

from backend.src.validators.omdb_validator import (
    validar_busqueda_omdb,
    validar_detalle_omdb,
    validar_importacion_omdb,
)

peliculas_bp = Blueprint("peliculas", __name__)

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
        logging.exception("Error al listar películas")
        return jsonify({"error": "No se pudieron obtener las películas"}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

@peliculas_bp.route("/peliculas", methods=["POST"])
@admin_required
def crear_pelicula_manual(id_usuario):
    datos = request.get_json(silent=True)
    datos_validados, error = validar_pelicula(datos)

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

        logging.exception("Error al crear película")
        return jsonify({"error": "No se pudo crear la película"}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

@peliculas_bp.route("/peliculas/<int:id_pelicula>", methods=["PUT"])
@admin_required
def editar_pelicula_manual(id_usuario, id_pelicula):
    datos = request.get_json(silent=True)
    datos_validados, error = validar_pelicula(datos)

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
            datos_validados
        )

        if resultado["status"] < 400:
            conexion.commit()
        else:
            conexion.rollback()

        return jsonify(resultado["data"]), resultado["status"]

    except MySQLError:
        if conexion is not None:
            conexion.rollback()

        logging.exception("Error al editar película")
        return jsonify({"error": "No se pudo editar la película"}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()

@peliculas_bp.route("/peliculas/omdb/buscar", methods=["GET"])
@admin_required
def buscar_peliculas_omdb(id_usuario):
    titulo = request.args.get("titulo")
    error = validar_busqueda_omdb(titulo)

    if error:
        return jsonify({"error": error}), 400

    try:
        resultado = buscar_peliculas(titulo.strip())
        return jsonify(resultado), 200

    except TimeoutError as error:
        logging.exception("Tiempo de espera agotado en OMDb")
        return jsonify({"error": str(error)}), 504

    except ConnectionError as error:
        logging.exception("Error de conexión con OMDb")
        return jsonify({"error": str(error)}), 502

    except ValueError as error:
        logging.exception("Error en búsqueda OMDb")
        return jsonify({"error": str(error)}), 404

    except RuntimeError as error:
        logging.exception("Error al consultar OMDb")
        return jsonify({"error": str(error)}), 502

@peliculas_bp.route("/peliculas/omdb/detalle", methods=["GET"])
@admin_required
def obtener_detalle_omdb(id_usuario):
    imdb_id = request.args.get("imdb_id")
    error = validar_detalle_omdb(imdb_id)

    if error:
        return jsonify({"error": error}), 400

    try:
        resultado = obtener_pelicula_por_id(imdb_id.strip())
        return jsonify(resultado), 200

    except TimeoutError as error:
        logging.exception("Tiempo de espera agotado en OMDb")
        return jsonify({"error": str(error)}), 504

    except ConnectionError as error:
        logging.exception("Error de conexión con OMDb")
        return jsonify({"error": str(error)}), 502

    except ValueError as error:
        logging.exception("Error al obtener película de OMDb")
        return jsonify({"error": str(error)}), 404

    except RuntimeError as error:
        logging.exception("Error al consultar OMDb")
        return jsonify({"error": str(error)}), 502

@peliculas_bp.route("/peliculas/omdb/importar", methods=["POST"])
@admin_required
def importar_pelicula_omdb(id_usuario):
    datos = request.get_json(silent=True)
    error = validar_importacion_omdb(datos)

    if error:
        return jsonify({"error": error}), 400

    conexion = None
    cursor = None

    try:
        pelicula_omdb = obtener_pelicula_por_id(
            datos["imdb_id"].strip()
        )

        pelicula = preparar_pelicula_para_guardar(pelicula_omdb)

        if not pelicula["poster"]:
            pelicula["poster"] = "/static/img/poster-no-disponible.jpg"

        conexion = get_connection()
        cursor = conexion.cursor(dictionary=True, buffered=True)

        resultado = guardar_pelicula(cursor, pelicula)

        if not resultado["exito"]:
            conexion.rollback()
            return jsonify({"error": resultado["error"]}), 400

        conexion.commit()

        return jsonify({
            "mensaje": "Película importada correctamente",
            "id_pelicula": resultado["id"],
            "accion": resultado["accion"]
        }), 201

    except MySQLError:
        if conexion is not None:
            conexion.rollback()

        logging.exception("Error al guardar película importada")
        return jsonify({"error": "No se pudo guardar la película"}), 500

    except TimeoutError as error:
        logging.exception("Tiempo de espera agotado en OMDb")
        return jsonify({"error": str(error)}), 504

    except ConnectionError as error:
        logging.exception("Error de conexión con OMDb")
        return jsonify({"error": str(error)}), 502

    except ValueError as error:
        logging.exception("Error al procesar película de OMDb")
        return jsonify({"error": str(error)}), 404

    except RuntimeError as error:
        logging.exception("Error al consultar OMDb")
        return jsonify({"error": str(error)}), 502

    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None:
            conexion.close()
