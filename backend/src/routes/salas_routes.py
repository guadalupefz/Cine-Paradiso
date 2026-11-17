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
)

salas_bp = Blueprint("salas", __name__)


@salas_bp.delete("/salas/<int:id_sala>")
@admin_required
def eliminar_sala(id_usuario, id_sala):
    resultado, estado = eliminar_estructura("sala", id_sala)
    return jsonify(resultado), estado


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

    conn = None

    try:
        conn = get_connection()

        with conn.cursor(dictionary=True) as cursor:
            id_sala = crear_sala_servicio(
                cursor,
                id_local,
                data["nombre"].strip(),
                data["capacidad"],
            )

        if id_sala is None:
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
