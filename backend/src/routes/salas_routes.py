import mysql.connector
from flask import Blueprint, jsonify, request

from backend.db.db import get_connection
from backend.seguridad import admin_required
from backend.src.services.eliminacion_estructura_service import eliminar_estructura
from backend.src.services.salas_service import (
    obtener_salas_por_local,
    crear_sala as crear_sala_servicio,
)
from backend.src.validators.salas_validator import (
    validar_datos_sala,
    validar_id_local,
    validar_id_sala,
)

salas_bp = Blueprint("salas", __name__)


@salas_bp.delete("/salas/<int:id_sala>")
@admin_required
def eliminar_sala(id_usuario, id_sala):
    error = validar_id_sala(id_sala)
    if error:
        return jsonify({"error": error}), 400

    conn = None

    try:
        conn = get_connection()

        with conn.cursor(dictionary=True) as cursor:
            resultado = eliminar_estructura(cursor, "sala", id_sala)

        if resultado == "eliminado":
            conn.commit()
            return jsonify({
                "mensaje": "Sala eliminada junto con sus butacas."
            }), 200

        conn.rollback()

        if resultado == "no_existe":
            return jsonify({
                "error": "La sala indicada no existe."
            }), 404

        if resultado == "en_uso":
            return jsonify({
                "error": "No se puede eliminar: hay funciones o entradas asociadas."
            }), 409

        return jsonify({
            "error": "No se pudo completar la eliminación. Volvé a cargar la página."
        }), 409

    except mysql.connector.IntegrityError:
        if conn is not None:
            conn.rollback()

        return jsonify({
            "error": "No se puede eliminar: existen registros asociados que deben conservarse."
        }), 409

    except mysql.connector.Error as error:
        if conn is not None:
            conn.rollback()

        if error.errno in (1205, 1213):
            return jsonify({
                "error": "El registro está siendo utilizado. Intentá nuevamente."
            }), 409

        return jsonify({"error": "No se pudo eliminar la sala."}), 500

    finally:
        if conn is not None:
            conn.close()


@salas_bp.route("/locales/<int:id_local>/salas", methods=["GET"])
def listar_salas(id_local):
    error = validar_id_local(id_local)
    if error:
        return jsonify({"error": error}), 400

    conn = None

    try:
        conn = get_connection()

        with conn.cursor(dictionary=True) as cursor:
            salas = obtener_salas_por_local(cursor, id_local)

        if salas is None:
            return jsonify({"error": "No existe el local indicado."}), 404

        return jsonify({"salas": salas}), 200

    except mysql.connector.Error:
        return jsonify({"error": "No se pudieron consultar las salas."}), 500

    finally:
        if conn is not None:
            conn.close()


@salas_bp.route("/locales/<int:id_local>/salas", methods=["POST"])
@admin_required
def crear_sala(id_usuario, id_local):
    error = validar_id_local(id_local)
    if error:
        return jsonify({"error": error}), 400

    data = request.get_json(silent=True)
    error = validar_datos_sala(data)

    if error:
        return jsonify({"error": error}), 400

    nombre = data["nombre"].strip()
    capacidad = data["capacidad"]

    conn = None

    try:
        conn = get_connection()

        with conn.cursor(dictionary=True) as cursor:
            id_sala = crear_sala_servicio(
                cursor,
                id_local,
                nombre,
                capacidad,
            )

        if id_sala is None:
            conn.rollback()
            return jsonify({"error": "No existe el local indicado."}), 404

        conn.commit()

        return jsonify({
            "mensaje": "Sala creada correctamente.",
            "id_sala": id_sala
        }), 201

    except mysql.connector.IntegrityError:
        if conn is not None:
            conn.rollback()

        return jsonify({
            "error": "Ya existe una sala con ese nombre en el local."
        }), 409

    except mysql.connector.Error:
        if conn is not None:
            conn.rollback()

        return jsonify({"error": "No se pudo crear la sala."}), 500

    finally:
        if conn is not None:
            conn.close()