from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from backend.autenticacion import revocar_token
import mysql.connector
from werkzeug.security import check_password_hash
from backend.db.db import get_connection
from backend.seguridad import cualquier_logueado
from backend.src.repositories.auth_repository import buscar_credenciales, obtener_perfil
from backend.src.validators.auth_validator import validar_datos_registro
from backend.src.services.auth_service import registrar_usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/registro', methods=['POST'])
def registro():
    try:
        data = request.get_json(silent=True)

        if data is None:
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

        usuario, errores_srv = registrar_usuario(
            nombre=data.get('nombre', '').strip(),
            apellido=data.get('apellido', '').strip(),
            email=data.get('email', '').strip().lower(),
            password=data.get('password', '')
        )

        if errores_srv:
            return jsonify({'errors': errores_srv}), 409

        return jsonify({
            'message': 'Usuario registrado exitosamente.',
            'usuario': usuario
        }), 201

    except mysql.connector.IntegrityError:
        return jsonify({'error': 'El email ya está registrado.'}), 409

    except Exception:
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


@auth_bp.post("/auth/login")
def login():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "Se esperaba un objeto JSON"}), 400
    email, password = datos.get("email"), datos.get("password")
    if not isinstance(email, str) or not email.strip() or not isinstance(password, str) or not password or len(password) > 256:
        return jsonify({"error": "Datos inválidos"}), 400
    try:
        conexion = get_connection()
        try:
            with conexion.cursor(dictionary=True) as cursor:
                usuario = buscar_credenciales(cursor, email.strip().lower())
        finally:
            conexion.close()
    except mysql.connector.Error:
        return jsonify({"error": "No se pudo iniciar sesión"}), 500
    if usuario is None or not check_password_hash(usuario["password_hash"], password):
        return jsonify({"error": "Credenciales inválidas"}), 401
    session.clear()
    token = create_access_token(identity=str(usuario["id_usuario"]))
    publico = {clave: valor for clave, valor in usuario.items() if clave != "password_hash"}
    respuesta = jsonify({"mensaje": "Sesión iniciada", "usuario": publico, "access_token": token, "token_type": "Bearer", "expires_in": 7200})
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta, 200

@auth_bp.post("/auth/logout")
@jwt_required()
def logout():
    revocar_token(get_jwt())
    session.clear()
    return jsonify({"mensaje": "Sesión cerrada"}), 200

@auth_bp.get("/usuarios/me")
@cualquier_logueado
def perfil(id_usuario):
    try:
        conexion = get_connection()
        try:
            with conexion.cursor(dictionary=True) as cursor:
                usuario = obtener_perfil(cursor, id_usuario)
        finally:
            conexion.close()
    except mysql.connector.Error:
        return jsonify({"error": "No se pudo consultar el perfil"}), 500
    return jsonify(usuario), 200
