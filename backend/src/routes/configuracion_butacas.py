from flask_jwt_extended import jwt_required
import mysql.connector

from flask import Blueprint, jsonify, request

from backend.db.db import get_connection
from backend.seguridad import verificar_acceso
from backend.src.services.butacas_service import configurar_butacas_servicio
from backend.src.validators.butacas_validator import validar_butacas

configuracion_butacas_bp = Blueprint("configuracion_butacas", __name__)


@configuracion_butacas_bp.route("/salas/<int:id_sala>/butacas", methods=["POST"])
@jwt_required()
def configurar_butacas(id_sala):
    id_usuario, respuesta_acceso = verificar_acceso(('administrador',))
    if respuesta_acceso is not None:
        return respuesta_acceso

    if id_sala <= 0:
        return jsonify({"error": "El ID de la sala debe ser positivo."}), 400

    data = request.get_json(silent=True)
    butacas, error = validar_butacas(data)

    if error:
        return jsonify({"error": error}), 400

    conn = None

    try:
        conn = get_connection()
        conn.start_transaction()

        with conn.cursor(dictionary=True) as cursor:
            respuesta, error = configurar_butacas_servicio(
                cursor, id_sala, butacas
            )

        if error:
            conn.rollback()

            if error == "SALA_INEXISTENTE":
                return jsonify({"error": "No existe la sala indicada."}), 404

            if error == "CAPACIDAD_INVALIDA":
                return jsonify({
                    "error": "La cantidad de butacas debe coincidir con la capacidad de la sala.",
                    **respuesta
                }), 400

            if error == "BUTACAS_YA_CONFIGURADAS":
                return jsonify({
                    "error": "La sala ya tiene butacas configuradas."
                }), 409

        conn.commit()
        return jsonify(respuesta), 201

    except mysql.connector.Error:
        if conn is not None:
            conn.rollback()
        return jsonify({
            "error": "No se pudieron configurar las butacas."
        }), 500

    finally:
        if conn is not None:
            conn.close()
