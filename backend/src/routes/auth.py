from flask import Blueprint, jsonify, request, session
from mysql.connector import Error as DatabaseError
from werkzeug.security import check_password_hash

from src.db import get_db_connection


auth_routes = Blueprint("auth", __name__)


@auth_routes.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Se requiere un cuerpo JSON"}), 400

    email = data.get("email")
    password = data.get("password")
    if (
        not isinstance(email, str)
        or not isinstance(password, str)
        or not email.strip()
        or not password
    ):
        return jsonify({"error": "Email y password son obligatorios"}), 400
    email = email.strip()

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id_usuario, nombre, email, password_hash, rol
            FROM usuario
            WHERE email = %s
            """,
            (email,),
        )
        user = cursor.fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Credenciales invalidas"}), 401

        session.clear()
        session["id_usuario"] = user["id_usuario"]
        session["rol"] = user["rol"]
        session["nombre"] = user["nombre"]

        return jsonify({
            "id_usuario": user["id_usuario"],
            "nombre": user["nombre"],
            "email": user["email"],
            "rol": user["rol"],
        }), 200
    except DatabaseError:
        return jsonify({"error": "Error al consultar la base de datos"}), 500
    except Exception:
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn is not None and conn.is_connected():
            try:
                conn.close()
            except Exception:
                pass


@auth_routes.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"mensaje": "Sesion cerrada"}), 200


@auth_routes.route("/usuarios/me", methods=["GET"])
def current_user():
    required_keys = {"id_usuario", "nombre", "rol"}
    if not required_keys.issubset(session.keys()):
        session.clear()
        return jsonify({"error": "No autenticado"}), 401

    return jsonify({
        "id_usuario": session["id_usuario"],
        "nombre": session["nombre"],
        "rol": session["rol"],
    }), 200
