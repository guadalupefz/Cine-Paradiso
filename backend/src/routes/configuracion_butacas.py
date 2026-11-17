from flask import Blueprint, jsonify, request

from backend.seguridad import admin_required
from backend.src.services.butacas_service import configurar_butacas_servicio
from backend.src.validators.butacas_validator import validar_butacas

configuracion_butacas_bp = Blueprint("configuracion_butacas", __name__)


@configuracion_butacas_bp.route("/salas/<int:id_sala>/butacas", methods=["POST"])
@admin_required
def configurar_butacas(id_usuario, id_sala):
    if id_sala <= 0:
        return jsonify({"error": "El ID de la sala debe ser positivo."}), 400

    data = request.get_json(silent=True)
    butacas, error = validar_butacas(data)

    if error:
        return jsonify({"error": error}), 400

    respuesta, codigo = configurar_butacas_servicio(id_sala, butacas)

    return jsonify(respuesta), codigo
