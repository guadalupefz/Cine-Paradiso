from flask import Blueprint, jsonify, request
from src.validators.reservas_validator import validar_datos_reserva
from src.services.reservas_service import crear_reserva
from backend.seguridad import cliente_required

reservas_bp = Blueprint("reservas", __name__)

@reservas_bp.route("/funciones/<int:id_funcion>/reservas", methods=["POST"])
@cliente_required
def registrar_reserva(id_usuario, id_funcion):

    data = request.get_json(silent=True) or {}

    errores_val = validar_datos_reserva(id_funcion, data)

    if errores_val:
        return jsonify({"errors": errores_val}), 400

    reserva, error = crear_reserva(
        id_usuario=id_usuario,
        id_funcion=id_funcion,
        lista_id_butacas=data["butacas"],
        servicios=data.get("servicios", [])
    )

    if error:
        status_code = error.pop("status_code", 400)
        return jsonify(error), status_code

    return jsonify({
        "mensaje": "Reserva efectuada correctamente.",
        "reserva": reserva
    }), 201