from werkzeug.security import generate_password_hash
from src.repositories.auth_repository import obtener_usuario_por_email, crear_usuario

def registrar_usuario(nombre, apellido, email, password):
    
    usuario_existente = obtener_usuario_por_email(email)
    if usuario_existente:
        return None, [{
            'code': 'EMAIL_DUPLICADO',
            'message': 'El correo electrónico ya se encuentra registrado.',
            'level': 'error'
        }]
    
    pwd_hash = generate_password_hash(password)

    rol_seguro = 'cliente'

    id_creado = crear_usuario(nombre, apellido, email, pwd_hash, rol_seguro)

    usuario_publico = {
        'id_usuario': id_creado,
        'nombre': nombre,
        'apellido': apellido,
        'email': email,
        'rol': rol_seguro
    }

    return usuario_publico, []
