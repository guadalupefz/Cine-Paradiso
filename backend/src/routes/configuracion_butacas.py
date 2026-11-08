import mysql.connector
from flask import Blueprint, jsonify, request

from backend.db.db import get_connection
from backend.seguridad import admin_required

configuracion_butacas_bp = Blueprint("configuracion_butacas", __name__)


@configuracion_butacas_bp.route("/salas/<int:id_sala>/butacas", methods=["POST"])
@admin_required
def configurar_butacas(id_usuario, id_sala):
    if id_sala <= 0:
        return jsonify({"error": "El ID de la sala debe ser positivo."}), 400

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not isinstance(data.get("butacas"), list):
        return jsonify({"error": "Se requiere una lista de butacas."}), 400

    butacas = data["butacas"]

    if not butacas:
        return jsonify({"error": "La sala debe tener al menos una butaca."}), 400

    for butaca in butacas:
        if not isinstance(butaca, dict):
            return jsonify({"error": "Cada butaca debe tener fila y número."}), 400

        fila = butaca.get("fila")
        numero = butaca.get("numero")

        if (
            not isinstance(fila, str)
            or not fila.strip()
            or len(fila.strip()) > 5
            or not fila.strip().isalpha()
        ):
            return jsonify({
                "error": "La fila debe contener entre 1 y 5 letras."
            }), 400

        if type(numero) is not int or numero <= 0:
            return jsonify({"error": "El número de butaca debe ser positivo."}), 400

    claves = [(b["fila"].strip().upper(), b["numero"]) for b in butacas]

    if len(claves) != len(set(claves)):
        return jsonify({"error": "No puede haber butacas repetidas."}), 400

    conn = None
    try:
        conn = get_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT capacidad FROM sala WHERE id_sala = %s",
                (id_sala,)
            )
            sala = cursor.fetchone()

            if sala is None:
                return jsonify({"error": "No existe la sala indicada."}), 404

            if len(butacas) != sala["capacidad"]:
                return jsonify({
                    "error": "La cantidad de butacas debe coincidir con la capacidad de la sala.",
                    "capacidad": sala["capacidad"],
                    "cantidad_butacas": len(butacas)
                }), 400

            cursor.execute(
                "SELECT COUNT(*) AS cantidad FROM butaca WHERE id_sala = %s",
                (id_sala,)
            )
            if cursor.fetchone()["cantidad"] > 0:
                return jsonify({"error": "La sala ya tiene butacas configuradas."}), 409

            cursor.executemany(
                "INSERT INTO butaca (id_sala, fila, numero) VALUES (%s, %s, %s)",
                [(id_sala, fila, numero) for fila, numero in claves]
            )

        conn.commit()
        return jsonify({
            "mensaje": "Butacas configuradas correctamente.",
            "id_sala": id_sala,
            "cantidad": len(butacas)
        }), 201

    except mysql.connector.Error:
        if conn is not None:
            conn.rollback()
        return jsonify({"error": "No se pudieron configurar las butacas."}), 500
    finally:
        if conn is not None:
            conn.close()
