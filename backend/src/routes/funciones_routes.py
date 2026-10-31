from datetime import datetime
from decimal import Decimal, InvalidOperation

import mysql.connector
from flask import Blueprint, jsonify, request

from src.db import get_connection
from src.repositories.funciones_repository import (
    modificar_funcion, obtener_funciones)

funciones_bp = Blueprint("funciones", __name__)


@funciones_bp.route("/funciones", methods=["GET"])
def listar_funciones():
    conn = None

    try:
        conn = get_connection()

        with conn.cursor(dictionary=True) as cursor:
            funciones = obtener_funciones(cursor)

        return jsonify({"funciones": funciones}), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudieron consultar las funciones."
        }), 500

    except Exception:
        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "Ocurrió un error interno en el servidor."
        }), 500

    finally:
        if conn is not None:
            conn.close()


@funciones_bp.route("/funciones/<int:id_funcion>", methods=["PUT"])
def actualizar_funcion(id_funcion):
    if id_funcion <= 0:
        return jsonify({
            "error": "ID_FUNCION_INVALIDO",
            "mensaje": "El ID debe ser positivo."
        }), 400

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "JSON_INVALIDO",
            "mensaje": "Se requiere un cuerpo JSON válido."
        }), 400

    campos = [
        "id_pelicula",
        "id_sala",
        "fecha_hora_inicio",
        "precio_base"
    ]

    faltantes = [campo for campo in campos if campo not in data]

    if faltantes:
        return jsonify({
            "error": "DATOS_INCOMPLETOS",
            "campos_faltantes": faltantes
        }), 400

    try:
        if isinstance(data["id_pelicula"], bool):
            raise ValueError

        if isinstance(data["id_sala"], bool):
            raise ValueError

        id_pelicula = int(data["id_pelicula"])
        id_sala = int(data["id_sala"])

        if id_pelicula <= 0 or id_sala <= 0:
            raise ValueError

        fecha_hora = datetime.fromisoformat(
            str(data["fecha_hora_inicio"])
        )

        precio = Decimal(str(data["precio_base"]))

        if not precio.is_finite() or precio < 0:
            raise ValueError

        if precio.as_tuple().exponent < -2:
            raise ValueError

    except (ValueError, TypeError, InvalidOperation):
        return jsonify({
            "error": "DATOS_INVALIDOS",
            "mensaje": (
                "Verificá los IDs, la fecha y el precio. "
                "El precio debe ser no negativo y tener "
                "como máximo dos decimales."
            )
        }), 400

    conn = None

    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id_funcion FROM funcion WHERE id_funcion = %s",
                (id_funcion,)
            )

            if cursor.fetchone() is None:
                return jsonify({
                    "error": "FUNCION_NO_ENCONTRADA",
                    "mensaje": "No existe una función con ese ID."
                }), 404

            cursor.execute(
                "SELECT id_pelicula FROM pelicula WHERE id_pelicula = %s",
                (id_pelicula,)
            )

            if cursor.fetchone() is None:
                return jsonify({
                    "error": "PELICULA_NO_ENCONTRADA",
                    "mensaje": "No existe la película indicada."
                }), 400

            cursor.execute(
                "SELECT id_sala FROM sala WHERE id_sala = %s",
                (id_sala,)
            )

            if cursor.fetchone() is None:
                return jsonify({
                    "error": "SALA_NO_ENCONTRADA",
                    "mensaje": "No existe la sala indicada."
                }), 400

            modificar_funcion(
                cursor,
                id_funcion,
                id_pelicula,
                id_sala,
                fecha_hora.strftime("%Y-%m-%d %H:%M:%S"),
                precio
            )

        conn.commit()

        return jsonify({
            "mensaje": "Función modificada correctamente.",
            "id_funcion": id_funcion
        }), 200

    except mysql.connector.IntegrityError:
        if conn is not None:
            conn.rollback()

        return jsonify({
            "error": "RESTRICCION_BASE_DATOS",
            "mensaje": "Los datos incumplen una restricción de la base de datos."
        }), 400

    except mysql.connector.Error:
        if conn is not None:
            conn.rollback()

        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudo modificar la función."
        }), 500

    except Exception:
        if conn is not None:
            conn.rollback()

        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "Ocurrió un error interno en el servidor."
        }), 500

    finally:
        if conn is not None:
            conn.close()
