"""Emision, verificacion y revocacion persistente de JWT."""
from datetime import datetime, timezone
from flask import jsonify
from flask_jwt_extended import JWTManager
from backend.db.db import get_connection

jwt = JWTManager()


@jwt.token_in_blocklist_loader
def token_revocado(cabecera, datos):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT jti FROM token_revocado WHERE jti = %s", (datos["jti"],))
            return cursor.fetchone() is not None
    finally:
        conexion.close()


def revocar_token(datos):
    vencimiento = datetime.fromtimestamp(datos["exp"], timezone.utc).replace(tzinfo=None)
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM token_revocado WHERE vence_en <= UTC_TIMESTAMP()")
            cursor.execute(
                "INSERT IGNORE INTO token_revocado (jti, vence_en) VALUES (%s, %s)",
                (datos["jti"], vencimiento),
            )
        conexion.commit()
    except Exception:
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
