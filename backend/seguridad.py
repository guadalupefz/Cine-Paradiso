import os
import datetime
import time
from functools import wraps
from flask import Flask, jsonify, request
import jwt
from dotenv import load_dotenv


load_dotenv()  
SECRET_KEY = os.getenv('JWT_SECRET_KEY')



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
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            
            auth_header = request.headers.get('Authorization')
            
            # Modificación 1: Validación simple de existencia
            if not auth_header:
                return jsonify({'error': 'No autorizado', 'message': 'Token ausente'}), 401
            
            partes = auth_header.split()
            
            # Modificación 2: Validación inteligente del formato y de la palabra 'bearer'
            if len(partes) != 2 or partes[0].lower() != 'bearer':
                return jsonify({'error': 'No autorizado', 'message': 'Formato de token inválido. Debe ser: Bearer <token>'}), 401
            
            token = partes[1]
            
            try:
                data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                user_role = data.get('role')      
                current_user = data.get('user_id')
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'No autorizado', 'message': 'El token ha expirado'}), 401
            except jwt.InvalidTokenError:
                # Modificación 3: Mensaje más descriptivo para el descarte de errores
                return jsonify({'error': 'No autorizado', 'message': 'Token inválido o firma corrupta'}), 401
            # Validación del Rol
            if user_role not in allowed_roles:
                return jsonify({'error': 'Prohibido', 'message': 'No tienes permisos para esta acción'}), 403

            return f(current_user, *args, **kwargs)
        return decorated
    return decorator

# Atajos limpios
admin_required = roles_required(['administrador'])
usuario_required = roles_required(['usuario'])
cualquier_logueado = roles_required(['administrador', 'usuario'])


