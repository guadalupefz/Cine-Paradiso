from flask_jwt_extended import jwt_required
import mysql.connector
from flask import Blueprint, jsonify, request

from backend.db.db import get_connection
from backend.seguridad import verificar_acceso
from backend.src.services.reservas_service import (
    abandonar_reserva_pendiente,
    crear_reserva,
    editar_reserva_pendiente,
    rechazar_reserva_pendiente,
)
from backend.src.validators.reservas_validator import validar_datos_reserva

reservas_bp = Blueprint("reservas", __name__)


def _error_base_datos(error, mensaje, toda_colision_duplicada):
    if error.errno == 1062 and (
        toda_colision_duplicada
        or "uq_entrada_ocupacion_activa" in str(error)
    ):
        return {
            "error": "BUTACAS_OCUPADAS",
            "mensaje": "Una o más butacas seleccionadas ya están reservadas o vendidas.",
            "status_code": 409,
        }

    if error.errno in (1205, 1213):
        return {
            "error": "CONFLICTO_RESERVA",
            "mensaje": "Otra operación está modificando la reserva. Volvé a intentar.",
            "status_code": 409,
        }

    return {
        "error": "ERROR_BASE_DATOS",
        "mensaje": mensaje,
        "status_code": 500,
    }


def _procesar_transaccion_reserva(
    operacion, mensaje_error, toda_colision_duplicada=False
):
    conexion = None
    try:
        conexion = get_connection()
        conexion.start_transaction()
        with conexion.cursor(dictionary=True) as cursor:
            reserva, error = operacion(cursor)

        if error:
            if error["error"] == "RESERVA_EXPIRADA":
                conexion.commit()
            else:
                conexion.rollback()
            return reserva, error

        conexion.commit()
        return reserva, None
    except mysql.connector.Error as error:
        if conexion is not None:
            conexion.rollback()
        return None, _error_base_datos(
            error, mensaje_error, toda_colision_duplicada
        )
    finally:
        if conexion is not None:
            conexion.close()


def _respuesta_error(error):
    contenido = {clave: valor for clave, valor in error.items() if clave != "status_code"}
    return jsonify(contenido), error.get("status_code", 400)


@reservas_bp.route("/funciones/<int:id_funcion>/reservas", methods=["POST"])
@jwt_required()
def registrar_reserva(id_funcion):
    id_usuario, respuesta_acceso = verificar_acceso(('cliente',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    data = request.get_json(silent=True) or {}
    errores_val = validar_datos_reserva(id_funcion, data)
    if errores_val:
        return jsonify({"errors": errores_val}), 400

    reserva, error = _procesar_transaccion_reserva(
        lambda cursor: crear_reserva(
            cursor,
            id_usuario=id_usuario,
            id_funcion=id_funcion,
            lista_id_butacas=data["butacas"],
            servicios=data.get("servicios", []),
        ),
        "Error en la base de datos al procesar la reserva.",
    )
    if error:
        return _respuesta_error(error)

    return jsonify({
        "mensaje": "Reserva efectuada correctamente.",
        "reserva": reserva,
    }), 201


@reservas_bp.route("/reservas/<int:id_compra>/rechazar", methods=["POST"])
@jwt_required()
def rechazar_reserva(id_compra):
    id_usuario, respuesta_acceso = verificar_acceso(('cliente',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    reserva, error = _procesar_transaccion_reserva(
        lambda cursor: rechazar_reserva_pendiente(
            cursor, id_compra, id_usuario
        ),
        "No se pudo rechazar la reserva.",
    )
    if error:
        return _respuesta_error(error)

    return jsonify({
        "mensaje": "La reserva fue rechazada correctamente.",
        "reserva": reserva,
    }), 200


@reservas_bp.route("/reservas/<int:id_compra>/abandonar", methods=["POST"])
@jwt_required()
def abandonar_reserva(id_compra):
    id_usuario, respuesta_acceso = verificar_acceso(('cliente',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    reserva, error = _procesar_transaccion_reserva(
        lambda cursor: abandonar_reserva_pendiente(
            cursor, id_compra, id_usuario
        ),
        "No se pudo abandonar la reserva.",
    )
    if error:
        return _respuesta_error(error)

    return jsonify({
        "mensaje": "La reserva fue abandonada correctamente.",
        "reserva": reserva,
    }), 200


@reservas_bp.route("/reservas/<int:id_compra>", methods=["PUT"])
@jwt_required()
def modificar_reserva(id_compra):
    id_usuario, respuesta_acceso = verificar_acceso(('cliente',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    data = request.get_json(silent=True) or {}
    errores_val = validar_datos_reserva(None, data)
    if errores_val:
        return jsonify({"errors": errores_val}), 400

    reserva, error = _procesar_transaccion_reserva(
        lambda cursor: editar_reserva_pendiente(
            cursor,
            id_compra=id_compra,
            id_usuario=id_usuario,
            lista_id_butacas=data["butacas"],
            servicios=data.get("servicios", []),
        ),
        "No se pudo editar la reserva.",
        toda_colision_duplicada=True,
    )
    if error:
        return _respuesta_error(error)

    return jsonify({
        "mensaje": "La reserva fue modificada correctamente.",
        "reserva": reserva,
    }), 200
