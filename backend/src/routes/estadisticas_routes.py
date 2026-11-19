from flask_jwt_extended import jwt_required
import mysql.connector
from flask import Blueprint, jsonify, request

from backend.db.db import get_connection
from backend.seguridad import verificar_acceso
from backend.src.validators.estadisticas_validator import validar_filtros_estadisticas
from backend.src.services.estadisticas_service import (
    consultar_ventas_service,
    consultar_ocupacion_service,
)

estadisticas_bp = Blueprint("estadisticas", __name__)


@estadisticas_bp.route("/estadisticas/ventas", methods=["GET"])
@jwt_required()
def consultar_estadisticas_ventas():
    id_usuario, respuesta_acceso = verificar_acceso(('administrador',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    desde, hasta, id_local, error = validar_filtros_estadisticas(request.args)

    if error:
        return jsonify({
            "error": "FILTRO_INVALIDO",
            "mensaje": error
        }), 400

    conexion = None

    try:
        conexion = get_connection()

        with conexion.cursor(dictionary=True) as cursor:
            estadisticas = consultar_ventas_service(
                cursor, desde, hasta, id_local
            )

        return jsonify(estadisticas), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudieron consultar las estadísticas de ventas."
        }), 500

    except Exception:
        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "Ocurrió un error interno al consultar las estadísticas."
        }), 500

    finally:
        if conexion is not None:
            conexion.close()


@estadisticas_bp.route("/estadisticas/ocupacion", methods=["GET"])
@jwt_required()
def consultar_estadisticas_ocupacion():
    id_usuario, respuesta_acceso = verificar_acceso(('administrador',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    desde, hasta, id_local, error = validar_filtros_estadisticas(request.args)

    if error:
        return jsonify({
            "error": "FILTRO_INVALIDO",
            "mensaje": error
        }), 400

    conexion = None

    try:
        conexion = get_connection()

        with conexion.cursor(dictionary=True) as cursor:
            estadisticas = consultar_ocupacion_service(
                cursor, desde, hasta, id_local
            )

        return jsonify(estadisticas), 200

    except mysql.connector.Error:
        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudieron consultar las estadísticas de ocupación."
        }), 500

    except Exception:
        return jsonify({
            "error": "ERROR_SERVIDOR",
            "mensaje": "Ocurrió un error interno al consultar las estadísticas."
        }), 500

    finally:
        if conexion is not None:
            conexion.close()
