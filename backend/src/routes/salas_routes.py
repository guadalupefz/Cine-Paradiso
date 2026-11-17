import mysql.connector
from flask import Blueprint, jsonify, request

from backend.db.db import get_connection
from backend.seguridad import admin_required
from backend.src.repositories.salas_repository import obtener_salas_por_local
from backend.src.services.eliminacion_estructura_service import eliminar_estructura
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
            cursor.execute(
                "SELECT id_local FROM local WHERE id_local = %s",
                (id_local,)
            )
            if cursor.fetchone() is None:
                return jsonify({"error": "No existe el local indicado."}), 404

            salas = obtener_salas_por_local(cursor, id_local)

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
            cursor.execute(
                "SELECT id_local FROM local WHERE id_local = %s",
                (id_local,)
            )
            if cursor.fetchone() is None:
                return jsonify({"error": "No existe el local indicado."}), 404

            cursor.execute(
                "INSERT INTO sala (id_local, nombre, capacidad) VALUES (%s, %s, %s)",
                (id_local, nombre, capacidad)
            )
            id_sala = cursor.lastrowid

        conn.commit()
        return jsonify({
            "mensaje": "Sala creada correctamente.",
            "id_sala": id_sala
        }), 201
    except mysql.connector.IntegrityError:
        if conn is not None:
            conn.rollback()
        return jsonify({"error": "Ya existe una sala con ese nombre en el local."}), 409
    except mysql.connector.Error:
        if conn is not None:
            conn.rollback()
        return jsonify({"error": "No se pudo crear la sala."}), 500
    finally:
        if conn is not None:
            conn.close()
