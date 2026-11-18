from flask import Blueprint, request, jsonify, send_file

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

    resultado, error = validar_qr_service(qr_token, id_funcion)

    if error:
        status = error.pop("status_code", 500)
        return jsonify(error), status

    return jsonify(resultado), 200


@qr_bp.route("/qr/<int:id_entrada>", methods=["GET"])
@cualquier_logueado
def ver_qr(id_usuario, id_entrada):
    archivo_imagen, error = obtener_qr_imagen_service(id_entrada, id_usuario)

    if error:
        status = error.pop("status_code", 404)
        return jsonify(error), status

    return send_file(archivo_imagen, mimetype="image/png")
