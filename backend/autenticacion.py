"""Configuración de JWT y revocación persistente al cerrar sesión."""
from datetime import datetime, timezone
from flask import jsonify
from flask_jwt_extended import JWTManager
from mysql.connector import Error, IntegrityError

from backend.db.db import get_connection
from backend.src.repositories.tokens_repository import (
    buscar_token_revocado, guardar_token_revocado, eliminar_tokens_vencidos,
)

jwt = JWTManager()
ERROR_CLAVE_DUPLICADA = 1062


@jwt.token_in_blocklist_loader
def token_revocado(cabecera, datos):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            return buscar_token_revocado(cursor, datos["jti"]) is not None
    finally:
        conexion.close()


def vencimiento_utc(datos):
    return datetime.fromtimestamp(datos["exp"], timezone.utc).replace(tzinfo=None)


def registrar_revocacion(cursor, datos):
    try:
        guardar_token_revocado(cursor, datos["jti"], vencimiento_utc(datos))
    except IntegrityError as error:
        if error.errno != ERROR_CLAVE_DUPLICADA:
            raise


def revocar_token(datos):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            eliminar_tokens_vencidos(cursor)
            registrar_revocacion(cursor, datos)
        conexion.commit()
    except Error:
        conexion.rollback()
        raise
    finally:
        conexion.close()


@jwt.unauthorized_loader
def falta_token(motivo):
    return jsonify({"error": "Debés iniciar sesión"}), 401


@jwt.invalid_token_loader
def token_invalido(motivo):
    return jsonify({"error": "La credencial no es válida"}), 401


@jwt.expired_token_loader
def token_vencido(cabecera, datos):
    return jsonify({"error": "La sesión venció. Iniciá sesión nuevamente"}), 401


@jwt.revoked_token_loader
def token_cerrado(cabecera, datos):
    return jsonify({"error": "La sesión ya fue cerrada"}), 401
