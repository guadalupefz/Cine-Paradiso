from io import BytesIO

import mysql.connector
from flask import Blueprint, request, jsonify, send_file

from backend.seguridad import admin_required, cualquier_logueado
from backend.db.db import get_connection

from backend.src.validators.qr_validator import validar_datos_qr

from backend.src.repositories.qr_repository import (
    validar_entrada,
    marcar_entrada_usada,
    obtener_entrada_para_qr
)

from backend.src.services.qr_service import (
    entrada_utilizada,
    compra_confirmada,
    funcion_correcta,
    horario_correcto,
    generar_qr
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

    conn = None

    try:
        conn = get_connection()
        conn.autocommit = False

        with conn.cursor(dictionary=True) as cursor:
            entrada = validar_entrada(cursor, qr_token)

            if entrada is None:
                return jsonify({
                    "error": "QR_NO_ENCONTRADO",
                    "mensaje": "No existe una entrada con ese qr"
                }), 404

            if entrada_utilizada(entrada):
                conn.rollback()
                return jsonify({
                    "error": "QR_YA_UTILIZADO",
                    "mensaje": "esta entrada ya se uso"
                }), 409

            if not compra_confirmada(entrada):
                return jsonify({
                    "error": "COMPRA_NO_CONFIRMADA",
                    "mensaje": "la compra no está confirmada"
                }), 409

            if not funcion_correcta(entrada, id_funcion):
                return jsonify({
                    "error": "FUNCION_INCORRECTA",
                    "mensaje": "la entrada no corresponde a esta funcion"
                }), 409

            if not horario_correcto(entrada):
                return jsonify({
                    "error": "HORARIO_INCORRECTO",
                    "mensaje": "la entrada está fuera del horario permitido"
                }), 409

            filas_actualizadas = marcar_entrada_usada(
                cursor, entrada["id_entrada"]
            )

            if filas_actualizadas != 1:
                conn.rollback()
                return jsonify({
                    "error": "QR_NO_ACTUALIZADO",
                    "mensaje": "no se pudo hacer el ingreso"
                }), 409

        conn.commit()

        return jsonify({
            "valida": True,
            "mensaje": "Entrada validada correctamente.",
            "id_entrada": entrada["id_entrada"]
        }), 200

    except mysql.connector.Error as error:

        if conn is not None:
            conn.rollback()

        return jsonify({
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudo validar la entrada."
        }), 500

    finally:
        if conn is not None:
            conn.close()





@qr_bp.route("/qr/<int:id_entrada>", methods=["GET"])
@cualquier_logueado
def ver_qr(id_usuario, id_entrada):
    conn = get_connection()

    try:
        with conn.cursor(dictionary=True) as cursor:
            entrada = obtener_entrada_para_qr(cursor, id_entrada, id_usuario)
    finally:
        conn.close()

    if entrada is None:
        return jsonify({"mensaje": "no se encontró la entrada"}), 404

    imagen = generar_qr(entrada["qr_token"])

    archivo = BytesIO()
    imagen.save(archivo, format="PNG")
    archivo.seek(0)

    return send_file(archivo, mimetype="image/png")