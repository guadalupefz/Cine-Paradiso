"""Autenticacion JWT y permisos consultados en la base de datos."""
import time
from functools import wraps
from math import ceil
from threading import Lock
import mysql.connector
from flask import current_app, jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from backend.db.db import get_connection

def crear_limitador():
    """Limita intentos por ruta e IP dentro de cada instancia de la aplicación."""
    bloqueo = Lock()

    def configurar_limite(max_dia=200, max_hora=50):
        def decorador(f):
            @wraps(f)
            def funcion_decorada(*args, **kwargs):
                clave = (request.endpoint, request.remote_addr)
                with bloqueo:
                    ahora = time.monotonic()
                    historiales = current_app.extensions.setdefault("limites_solicitudes", {})
                    accesos = [t for t in historiales.get(clave, []) if ahora - t < 86400]
                    historiales[clave] = accesos
                    accesos_hora = [t for t in accesos if ahora - t < 3600]
                    espera = 0
                    if len(accesos) >= max_dia:
                        espera = max(espera, ceil(86400 - (ahora - accesos[0])))
                    if len(accesos_hora) >= max_hora:
                        espera = max(espera, ceil(3600 - (ahora - accesos_hora[0])))
                    if espera:
                        return (
                            jsonify({"error": "Demasiados intentos. Intentá nuevamente más tarde."}),
                            429,
                            {"Retry-After": str(espera)},
                        )
                    accesos.append(ahora)

                return f(*args, **kwargs)
            return funcion_decorada
        return decorador

    return configurar_limite

limitar = crear_limitador()


def roles_required(allowed_roles):
    roles = {rol.strip().casefold() for rol in allowed_roles}
    def decorator(funcion):
        @wraps(funcion)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            identidad = get_jwt_identity()
            if not isinstance(identidad, str) or not identidad.isascii() or not identidad.isdecimal() or int(identidad) <= 0:
                return jsonify({"error": "La credencial no es válida"}), 401
            id_usuario = int(identidad)
            try:
                conexion = get_connection()
                try:
                    with conexion.cursor(dictionary=True) as cursor:
                        cursor.execute("SELECT id_usuario, rol FROM usuario WHERE id_usuario = %s", (id_usuario,))
                        usuario = cursor.fetchone()
                finally:
                    conexion.close()
            except mysql.connector.Error:
                return jsonify({"error": "No se pudo verificar el acceso"}), 500
            if usuario is None:
                return jsonify({"error": "Debés iniciar sesión"}), 401
            rol = usuario.get("rol")
            if not isinstance(rol, str) or rol.strip().casefold() not in roles:
                return jsonify({"error": "No tenés permisos para esta acción"}), 403
            return funcion(id_usuario, *args, **kwargs)
        return decorated
    return decorator

admin_required = roles_required(["administrador"])
cliente_required = roles_required(["cliente"])
usuario_required = cliente_required
cualquier_logueado = roles_required(["administrador", "cliente"])
