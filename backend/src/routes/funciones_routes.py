from flask import Blueprint, jsonify, request
import mysql.connector
from mysql.connector import Error as MySQLError

from backend.seguridad import admin_required
from backend.db.db import get_connection

from backend.src.services.funciones_service import (
    listar_funciones_servicio,
    crear_funcion_servicio,
    modificar_funcion_servicio,
)

from backend.src.repositories.funciones_repository import obtener_cartelera

from backend.src.validators.funciones_validator import  validar_datos_funcion


funciones_bp = Blueprint("funciones", __name__)


@funciones_bp.route("/funciones", methods=["GET"])
def listar_funciones_route():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        funciones = listar_funciones_servicio(
            cursor,
            solo_vigentes=request.args.get("vigentes") == "1"
        )

        return jsonify(funciones), 200

    except MySQLError:
        return jsonify({
            "error": "Error al consultar las funciones."
        }), 500

    except Exception:
        return jsonify({
            "error": "Error interno del servidor."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


@funciones_bp.route("/funciones", methods=["POST"])
@admin_required
def crear_funcion_route(id_usuario):
    data = request.get_json(silent=True)
    error = validar_datos_funcion(data)

    if error:
        return jsonify({"error": error}), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        id_funcion = crear_funcion_servicio(cursor, data)

        conn.commit()

        return jsonify({
            "mensaje": "Función creada exitosamente",
            "id_funcion": id_funcion,
        }), 201

    except MySQLError as err:
        if conn is not None:
            conn.rollback()

        if err.errno == 1452:
            return jsonify({
                "error": "Error de integridad referencial",
                "detalle": "La película o la sala especificada no existe en la base de datos.",
            }), 400

        return jsonify({
            "error": "No se pudo crear la función."
        }), 500

    except ValueError as err:
        if conn is not None:
            conn.rollback()

        return jsonify({"error": str(err)}), 400

    except Exception:
        if conn is not None:
            conn.rollback()

        return jsonify({
            "error": "Ocurrió un error al crear la función en la base de datos."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


@funciones_bp.route("/cartelera", methods=["GET"])
def consultar_cartelera():
    conn = None

    try:
        conn = get_connection()

        with conn.cursor(dictionary=True) as cursor:
            cartelera = obtener_cartelera(cursor)

        return jsonify({"cartelera": cartelera}), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudo consultar la cartelera.",
        }), 500

    except Exception:
        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "Ocurrió un error interno en el servidor.",
        }), 500

    finally:
        if conn is not None:
            conn.close()


@funciones_bp.route("/funciones/<int:id_funcion>", methods=["PUT"])
@admin_required
def actualizar_funcion(id_usuario, id_funcion):
    if id_funcion <= 0:
        return jsonify({
            "error": "ID_FUNCION_INVALIDO",
            "mensaje": "El ID debe ser positivo.",
        }), 400

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "JSON_INVALIDO",
            "mensaje": "Se requiere un cuerpo JSON válido.",
        }), 400

    campos = [
        "id_pelicula",
        "id_sala",
        "fecha_hora_inicio",
        "precio_base",
    ]

    faltantes = [campo for campo in campos if campo not in data]

    if faltantes:
        return jsonify({
            "error": "DATOS_INCOMPLETOS",
            "campos_faltantes": faltantes,
        }), 400

    error = validar_datos_funcion(data)

    if error:
        return jsonify({
            "error": "DATOS_INVALIDOS",
            "mensaje": error,
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        modificar_funcion_servicio(cursor, id_funcion, data)

        conn.commit()

        return jsonify({
            "mensaje": "Función modificada correctamente.",
            "id_funcion": id_funcion,
        }), 200

    except LookupError as err:
        if conn is not None:
            conn.rollback()

        return jsonify({
            "error": "FUNCION_NO_ENCONTRADA",
            "mensaje": str(err),
        }), 404

    except ValueError as err:
        if conn is not None:
            conn.rollback()

        return jsonify({
            "error": "ERROR_VALIDACION",
            "mensaje": str(err),
        }), 400

    except mysql.connector.IntegrityError:
        if conn is not None:
            conn.rollback()

        return jsonify({
            "error": "RESTRICCION_BASE_DATOS",
            "mensaje": "Los datos incumplen una restricción de la base de datos.",
        }), 400

    except MySQLError:
        if conn is not None:
            conn.rollback()

        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudo modificar la función.",
        }), 500

    except Exception:
        if conn is not None:
            conn.rollback()

        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "Ocurrió un error interno en el servidor.",
        }), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()