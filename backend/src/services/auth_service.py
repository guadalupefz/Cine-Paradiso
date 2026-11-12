from werkzeug.security import generate_password_hash, check_password_hash

from backend.src.repositories.auth_repository import (
    obtener_usuario_por_email,
    crear_usuario,
    buscar_credenciales,
    obtener_perfil
)


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


def autenticar_usuario(email, password):

    usuario = buscar_credenciales(email)

    if usuario is None:
        return None

    if not check_password_hash(usuario['password_hash'], password):
        return None

    return usuario


def obtener_perfil_usuario(id_usuario):

    usuario = obtener_perfil(id_usuario)

    return usuario
