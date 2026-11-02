from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from mysql.connector import Error as DatabaseError

from src.db import get_db_connection

#voy a explicar algunas cosas de JWT porque es nuevo
"""
jwt_required: es un decorador que exige que el usuario 
tenga un token JWT válido para acceder al endpoint.

get_jwt_identity: permite obtener la identidad del usuario que está 
guardada dentro del token JWT. En nuestro caso, es el id_usuario.
"""

compras_routes = Blueprint("compras", __name__)

@compras_routes.route("/compras", methods=["GET"])
@jwt_required() #este decorador se coloca antes de cada función para impedir que alguien sin un token válido pueda ejecutarla
def listar_compras():
    id_usuario = int(get_jwt_identity())

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
        SELECT
            c.id_compra,
            c.fecha_hora,
            c.total,
            c.estado,
            b.fila,
            b.numero
        FROM compra c
        JOIN entrada e ON c.id_compra = e.id_compra
        JOIN butaca b ON e.id_butaca = b.id_butaca
        WHERE c.id_usuario = %s
        ORDER BY c.fecha_hora DESC
        """, (id_usuario,))

        compras = cursor.fetchall()

        return jsonify({"compras": compras}), 200

    except DatabaseError:
        return jsonify({"error": "Error al consultar las compras"}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()

@compras_routes.route("/compras/<int:id_compra>/cancelar", methods=["POST"])
@jwt_required()
def cancelar_compra(id_compra):
    id_usuario = int(get_jwt_identity())

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id_compra, estado
            FROM compra
            WHERE id_compra = %s AND id_usuario = %s
            FOR UPDATE
        """, (id_compra, id_usuario))

        compra = cursor.fetchone()

        if not compra:
            conn.rollback()
            return jsonify({"error": "Compra no encontrada"}), 404

        if compra["estado"].lower() != "confirmada":
            conn.rollback()
            return jsonify({
                "error": "La compra no está confirmada o ya fue cancelada"
            }), 400

        cursor.execute("""
            SELECT f.fecha_hora_inicio
            FROM entrada e
            JOIN funcion f ON e.id_funcion = f.id_funcion
            WHERE e.id_compra = %s
            FOR UPDATE
        """, (id_compra,))

        funciones = cursor.fetchall()

        if not funciones:
            conn.rollback()
            return jsonify({"error": "La compra no tiene entradas"}), 400

        cursor.execute("""
            SELECT COUNT(*) AS cantidad
            FROM entrada
            WHERE id_compra = %s
        """, (id_compra,))

        cantidad = cursor.fetchone()["cantidad"]

        if cantidad == 0:
            conn.rollback()
            return jsonify({"error": "La compra no tiene entradas"}), 400

        cursor.execute("""
            SELECT COUNT(*) AS cantidad
            FROM entrada e
            JOIN funcion f ON e.id_funcion = f.id_funcion
            WHERE e.id_compra = %s
              AND f.fecha_hora_inicio <= DATE_ADD(NOW(), INTERVAL 2 HOUR)
        """, (id_compra,))

        fuera_de_plazo = cursor.fetchone()["cantidad"]

        if fuera_de_plazo > 0:
            conn.rollback()
            return jsonify({
                "error": "No se puede cancelar: alguna función comienza dentro de las próximas dos horas o ya comenzó"
            }), 400

        cursor.execute("""
            UPDATE compra
            SET estado = 'cancelada'
            WHERE id_compra = %s AND id_usuario = %s
        """, (id_compra, id_usuario))

        conn.commit()

        return jsonify({
            "mensaje": "Compra cancelada correctamente",
            "id_compra": id_compra
        }), 200

    except DatabaseError:
        if conn is not None:
            conn.rollback()

        return jsonify({"error": "Error al cancelar la compra"}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()
