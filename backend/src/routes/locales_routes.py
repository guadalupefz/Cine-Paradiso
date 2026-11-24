from flask_jwt_extended import jwt_required
import mysql.connector
from flask import Blueprint, jsonify, request

from backend.db.db import get_connection
from backend.seguridad import verificar_acceso
from backend.src.repositories.locales_repository import (
    obtener_locales,
    crear_local,
)
from backend.src.services.eliminacion_estructura_service import eliminar_estructura
from backend.src.validators.locales_validator import (validar_datos_local, validar_id_local)


locales_bp = Blueprint("locales", __name__)


@locales_bp.delete("/locales/<int:id_local>")
@jwt_required()
def eliminar_local(id_local):

    id_usuario, respuesta_acceso = verificar_acceso(('administrador',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    error = validar_id_local(id_local)
    if error:
        return jsonify({"error": error}), 400

    conn = None
    try:
        conn = get_connection()

        with conn.cursor(dictionary=True) as cursor:
            resultado = eliminar_estructura(cursor, "local", id_local)

        if resultado == "eliminado":
            conn.commit()
            return jsonify({
                "mensaje": "Local eliminado junto con sus salas y butacas."
            }), 200

        conn.rollback()

        if resultado == "no_existe":
            return jsonify({
                "error": "El local indicado no existe."
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

        return jsonify({"error": "No se pudo eliminar el local."}), 500

    finally:
        if conn is not None:
            conn.close()


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
@jwt_required()
def crear_local_route():
    id_usuario, respuesta_acceso = verificar_acceso(('administrador',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    data = request.get_json(silent=True)

    error = validar_datos_local(data)
    if error:
        return jsonify({"error": error}), 400

    nombre = data["nombre"].strip()
    direccion = data["direccion"].strip()

    conn = None
    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            id_local = crear_local(cursor, nombre, direccion)

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
