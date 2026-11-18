import mysql.connector

from flask import Blueprint, request, jsonify, send_file

from backend.db.db import get_connection
from backend.seguridad import admin_required, cualquier_logueado
from backend.src.validators.qr_validator import validar_datos_qr
from backend.src.services.qr_service import (
    validar_qr_service,
    obtener_qr_imagen_service,
)

qr_bp = Blueprint("qr", __name__)


@qr_bp.route("/qr/validar", methods=["POST"])
@admin_required
def validar_qr(id_usuario):
    datos = request.get_json(silent=True)
    valido, mensaje = validar_datos_qr(datos)

    if not valido:
        return jsonify({
            "error": "QR_INVALIDO",
            "mensaje": mensaje
        }), 400

    qr_token = datos.get("qr_token").strip()
    id_funcion = datos.get("id_funcion")
    conexion = None

    try:
        conexion = get_connection()
        conexion.autocommit = False

        with conexion.cursor(dictionary=True) as cursor:
            resultado, error = validar_qr_service(
                cursor, qr_token, id_funcion
            )

        if error:
            conexion.rollback()
            estados = {
                "QR_NO_ENCONTRADO": 404,
                "QR_YA_UTILIZADO": 409,
                "COMPRA_NO_CONFIRMADA": 409,
                "FUNCION_INCORRECTA": 409,
                "HORARIO_INCORRECTO": 409,
                "QR_NO_ACTUALIZADO": 409,
            }
            return jsonify(error), estados.get(error["error"], 500)

        conexion.commit()
        return jsonify(resultado), 200

    except mysql.connector.Error:
        if conexion is not None:
            conexion.rollback()
        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudo validar la entrada."
        }), 500

    finally:
        if conexion is not None:
            conexion.close()


@qr_bp.route("/qr/<int:id_entrada>", methods=["GET"])
@cualquier_logueado
def ver_qr(id_usuario, id_entrada):
    conexion = None

    try:
        conexion = get_connection()

        with conexion.cursor(dictionary=True) as cursor:
            archivo_imagen, error = obtener_qr_imagen_service(
                cursor, id_entrada, id_usuario
            )

        if error:
            return jsonify(error), 404

        return send_file(archivo_imagen, mimetype="image/png")

    except mysql.connector.Error:
        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "Error de base de datos al generar la imagen del QR."
        }), 500

    finally:
        if conexion is not None:
            conexion.close()
