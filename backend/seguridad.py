"""Identidad y permisos del usuario autenticado."""
import mysql.connector
from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from backend.db.db import get_connection
from backend.src.repositories.auth_repository import obtener_perfil


def obtener_id_usuario():
    identidad = get_jwt_identity()
    if not isinstance(identidad, str) or not identidad.isascii() or not identidad.isdecimal():
        return None
    id_usuario = int(identidad)
    return id_usuario if id_usuario > 0 else None


def consultar_usuario(id_usuario):
    conexion = get_connection()
    try:
        with conexion.cursor(dictionary=True) as cursor:
            return obtener_perfil(cursor, id_usuario)
    finally:
        conexion.close()


def verificar_acceso(roles_permitidos):
    id_usuario = obtener_id_usuario()
    if id_usuario is None:
        return None, (jsonify({"error": "La credencial no es válida"}), 401)
    try:
        usuario = consultar_usuario(id_usuario)
    except mysql.connector.Error:
        return None, (jsonify({"error": "No se pudo verificar el acceso"}), 500)
    if usuario is None:
        return None, (jsonify({"error": "Debés iniciar sesión"}), 401)
    rol = usuario.get("rol")
    if not isinstance(rol, str) or rol.strip().casefold() not in roles_permitidos:
        return None, (jsonify({"error": "No tenés permisos para esta acción"}), 403)
    return id_usuario, None
