"""Autenticacion JWT y permisos consultados en la base de datos."""
import time
from functools import wraps
import mysql.connector
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from backend.db.db import get_connection

def crear_limitador():
    """
    Función constructora que encapsula las estructuras de datos.
    """
    historial_dia = {}
    historial_hora = {}

    def configurar_limite(max_dia=200, max_hora=50):
        """
        Esta capa recibe los parámetros específicos para cada endpoint.
        Si no le pasas nada, usa los valores por defecto (200 al día, 50 por hora).
        """
        def decorador(f):
            @wraps(f)
            def funcion_decorada(*args, **kwargs):
                ip = request.remote_addr
                ahora = time.time()

                # --- VALIDACIÓN LÍMITE DIARIO ---
                if ip not in historial_dia:
                    historial_dia[ip] = []
                historial_dia[ip] = [t for t in historial_dia[ip] if ahora - t < 86400]
                if len(historial_dia[ip]) >= max_dia:
                    return jsonify({"error": f"Límite diario superado (Máx {max_dia})"}), 429

                # --- VALIDACIÓN LÍMITE POR HORA ---
                if ip not in historial_hora:
                    historial_hora[ip] = []
                historial_hora[ip] = [t for t in historial_hora[ip] if ahora - t < 3600]
                if len(historial_hora[ip]) >= max_hora:
                    return jsonify({"error": f"Límite por hora superado (Máx {max_hora})"}), 429

                # Registrar accesos
                historial_dia[ip].append(ahora)
                historial_hora[ip].append(ahora)

                return f(*args, **kwargs)
            return funcion_decorada
        return decorador

    return configurar_limite

# Inicializamos la fábrica de límites
limitar = crear_limitador()


# @limitar()

# @limitar(max_dia=1000, max_hora=300)




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
