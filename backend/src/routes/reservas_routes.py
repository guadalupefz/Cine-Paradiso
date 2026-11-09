from flask import Blueprint, jsonify, request
from backend.src.validators.reservas_validator import validar_datos_reserva
from backend.src.services.reservas_service import crear_reserva, rechazar_reserva_pendiente, abandonar_reserva_pendiente, editar_reserva_pendiente
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

@reservas_bp.route("/reservas/<int:id_compra>/rechazar", methods=["POST"])
@cliente_required
def rechazar_reserva(id_usuario, id_compra):
    reserva, error = rechazar_reserva_pendiente(id_compra, id_usuario)

    if error:
        status_code = error.pop("status_code", 400)
        return jsonify(error), status_code

    return jsonify({
        "mensaje": "La reserva fue rechazada correctamente.",
        "reserva": reserva
    }), 200


@reservas_bp.route("/reservas/<int:id_compra>/abandonar", methods=["POST"])
@cliente_required
def abandonar_reserva(id_usuario, id_compra):
    reserva, error = abandonar_reserva_pendiente(id_compra, id_usuario)

    if error:
        status_code = error.pop("status_code", 400)
        return jsonify(error), status_code

    return jsonify({
        "mensaje": "La reserva fue abandonada correctamente.",
        "reserva": reserva
    }), 200



@reservas_bp.route("/reservas/<int:id_compra>", methods=["PUT"])
@cliente_required
def modificar_reserva(id_usuario, id_compra):
    data = request.get_json(silent=True)

    errores_val = validar_datos_reserva(None, data)

    if errores_val:
        return jsonify({"errors": errores_val}), 400

    reserva, error = editar_reserva_pendiente(
        id_compra=id_compra,
        id_usuario=id_usuario,
        lista_id_butacas=data["butacas"],
        servicios=data.get("servicios", [])
    )

    if error:
        status_code = error.pop("status_code", 400)
        return jsonify(error), status_code

    return jsonify({
        "mensaje": "La reserva fue modificada correctamente.",
        "reserva": reserva
    }), 200
