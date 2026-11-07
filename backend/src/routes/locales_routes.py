import mysql.connector
from flask import Blueprint, jsonify, request

from backend.db.db import get_connection
from backend.seguridad import admin_required
from backend.src.repositories.locales_repository import obtener_locales

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
        return jsonify({"error": "No se pudieron consultar los locales."}), 500
    finally:
        if conn is not None:
            conn.close()


@locales_bp.route("/locales", methods=["POST"])
@admin_required
def crear_local(id_usuario):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Se requiere un JSON válido."}), 400

    nombre = data.get("nombre")
    direccion = data.get("direccion")

    if not isinstance(nombre, str) or not nombre.strip() or len(nombre.strip()) > 100:
        return jsonify({"error": "El nombre es obligatorio y debe tener hasta 100 caracteres."}), 400

    if not isinstance(direccion, str) or not direccion.strip() or len(direccion.strip()) > 200:
        return jsonify({"error": "La dirección es obligatoria y debe tener hasta 200 caracteres."}), 400

    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO local (nombre, direccion) VALUES (%s, %s)",
                (nombre.strip(), direccion.strip())
            )
            id_local = cursor.lastrowid
        conn.commit()
        return jsonify({
            "mensaje": "Local creado correctamente.",
            "id_local": id_local
        }), 201
    except mysql.connector.Error:
        if conn is not None:
            conn.rollback()
        return jsonify({"error": "No se pudo crear el local."}), 500
    finally:
        if conn is not None:
            conn.close()
