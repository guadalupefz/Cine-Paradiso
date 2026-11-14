from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from backend.autenticacion import revocar_token
import mysql.connector
from backend.seguridad import cualquier_logueado
from backend.db.db import get_connection
from backend.src.validators.auth_validator import validar_datos_registro
from backend.src.services.auth_service import (registrar_usuario, autenticar_usuario,
obtener_perfil_usuario)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/auth/registro', methods=['POST'])
def registro():
    conn = None
    cursor = None

    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                'errors': [{
                    'code': 'JSON_INVALIDO',
                    'message': 'El cuerpo de la petición debe ser un JSON válido.',
                    'level': 'error'
                }]
            }), 400

        errores_val = validar_datos_registro(data)

        if errores_val:
            return jsonify({'errors': errores_val}), 400

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        usuario, errores_srv = registrar_usuario(
            cursor,
            nombre=data.get('nombre', '').strip(),
            apellido=data.get('apellido', '').strip(),
            email=data.get('email', '').strip().lower(),
            password=data.get('password', '')
        )

        if errores_srv:
            return jsonify({'errors': errores_srv}), 409

        conn.commit()

        return jsonify({
            'message': 'Usuario registrado exitosamente.',
            'usuario': usuario
        }), 201

    except mysql.connector.IntegrityError:
        if conn:
            conn.rollback()

        return jsonify({'error': 'El email ya está registrado.'}), 409

    except Exception:
        if conn:
            conn.rollback()

        return (
            jsonify({
                'errors': [{
                    'code': 'ERROR_SERVIDOR',
                    'message': 'Ocurrió un error interno en el servidor.',
                    'level': 'error',
                }]
            }),
            500,
        )

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()


@auth_bp.post("/auth/login")
def login():
    conn = None
    cursor = None

    datos = request.get_json(silent=True)

    if not isinstance(datos, dict):
        return jsonify({"error": "Se esperaba un objeto JSON"}), 400

    email = datos.get("email")
    password = datos.get("password")

    if (not isinstance(email, str) or not email.strip()
            or not isinstance(password, str) or not password
            or len(password) > 256):
        return jsonify({"error": "Datos inválidos"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        usuario = autenticar_usuario(
            cursor,
            email.strip().lower(),
            password
        )

    except mysql.connector.Error:
        return jsonify({"error": "No se pudo iniciar sesión"}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()

    if usuario is None:
        return jsonify({"error": "Credenciales inválidas"}), 401

    session.clear()

    token = create_access_token(identity=str(usuario["id_usuario"]))

    publico = {
        clave: valor
        for clave, valor in usuario.items()
        if clave != "password_hash"
    }

    respuesta = jsonify({
        "mensaje": "Sesión iniciada",
        "usuario": publico,
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 7200
    })

    respuesta.headers["Cache-Control"] = "no-store"

    return respuesta, 200

@auth_bp.get("/usuarios/me")
@cualquier_logueado
def perfil(id_usuario):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        usuario = obtener_perfil_usuario(cursor, id_usuario)

        if usuario is None:
            return jsonify({"error": "Usuario no encontrado"}), 404

        return jsonify(usuario), 200

    except mysql.connector.Error:
        return jsonify({"error": "No se pudo consultar el perfil"}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()

@auth_bp.post("/auth/logout")
@jwt_required()
def logout():
    revocar_token(get_jwt())
    session.clear()

    return jsonify({"mensaje": "Sesión cerrada"}), 200