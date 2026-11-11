import mysql.connector
from flask import Blueprint, jsonify, request

from backend.db.db import get_connection
from backend.seguridad import admin_required
from backend.src.repositories.salas_repository import obtener_salas_por_local
from backend.src.services.eliminacion_estructura_service import eliminar_estructura

salas_bp = Blueprint("salas", __name__)


@salas_bp.delete("/salas/<int:id_sala>")
@admin_required
def eliminar_sala(id_usuario, id_sala):
    resultado, estado = eliminar_estructura("sala", id_sala)
    return jsonify(resultado), estado


@salas_bp.route("/locales/<int:id_local>/salas", methods=["GET"])
def listar_salas(id_local):
    if id_local <= 0:
        return jsonify({"error": "El ID del local debe ser positivo."}), 400

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
    if id_local <= 0:
        return jsonify({"error": "El ID del local debe ser positivo."}), 400

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Se requiere un JSON válido."}), 400

    nombre = data.get("nombre")
    capacidad = data.get("capacidad")

    if not isinstance(nombre, str) or not nombre.strip() or len(nombre.strip()) > 50:
        return jsonify({"error": "El nombre de la sala es obligatorio y debe tener hasta 50 caracteres."}), 400

    if type(capacidad) is not int or capacidad <= 0:
        return jsonify({"error": "La capacidad debe ser un entero positivo."}), 400

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
                (id_local, nombre.strip(), capacidad)
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
