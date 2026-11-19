from flask_jwt_extended import jwt_required
from backend.seguridad import verificar_acceso
import mysql.connector
from flask import Blueprint, jsonify

from backend.db.db import get_connection
from backend.src.repositories.butacas_repository import obtener_butacas_por_funcion
from backend.src.repositories.funciones_repository import existe_funcion

mis_rutas = Blueprint('butacas', __name__)


@mis_rutas.route('/funciones/<int:id_funcion>/butacas', methods=['GET'])
@jwt_required()
def consultar_butacas(id_funcion):
    id_usuario, respuesta_acceso = verificar_acceso(('administrador', 'cliente'))
    if respuesta_acceso is not None:
        return respuesta_acceso

    if id_funcion <= 0:
        return jsonify({
            "error": "ID_FUNCION_INVALIDO",
            "mensaje": "El ID de la función debe ser positivo."
        }), 400

    conn = None

    try:
        conn = get_connection()

        with conn.cursor(dictionary=True) as cursor:
            if not existe_funcion(cursor, id_funcion):
                return jsonify({
                    "error": "FUNCION_NO_ENCONTRADA",
                    "mensaje": "No existe una función con ese ID."
                }), 404

            butacas = obtener_butacas_por_funcion(cursor, id_funcion)

        return jsonify({
            "id_funcion": id_funcion,
            "butacas": butacas
        }), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudieron consultar las butacas."
        }), 500

    except Exception:
        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "Ocurrió un error interno en el servidor."
        }), 500

    finally:
        if conn is not None:
            conn.close()
