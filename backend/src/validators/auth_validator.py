import re

# Patrón Regex estándar para correos electrónicos 
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def validar_datos_registro(data):
    errors = []
    nombre = data.get('nombre', '').strip()
    apellido = data.get('apellido', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    # 1. Validación de presencia
    if not nombre or not apellido or not email or not password:
        errors.append({
            'code': 'DATOS_INVALIDOS',
            'message': 'Todos los campos (nombre, apellido, email, password) son obligatorios.',
            'level': 'error'
        })

        return errors
    
    # 2. Validación de formato de Email con Regex
    if not re.match(EMAIL_REGEX, email):
        errors.append({
            'code': 'EMAIL_FORMATO_INVALIDO',
            'message': ( 'El correo electrónico ingresado no tiene un formato válido' 
            ' (ejemplo: usuario@dominio.com).' ), 
            'level': 'error', 
        })

        return errors