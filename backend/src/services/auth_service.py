from werkzeug.security import generate_password_hash

from src.repositories.usuario_repository import (
    obtener_usuario_por_email,
    crear_usuario
)


def registrar_usuario(cursor, nombre, apellido, email, password):


    if not nombre or not apellido or not email or not password:
        raise ValueError("Todos los campos son obligatorios")

    
    nombre = nombre.strip()
    apellido = apellido.strip()
    email = email.strip().lower()

    
    if not nombre or not apellido or not email:
        raise ValueError("Los campos no pueden estar vacíos")

    
    if "@" not in email or "." not in email:
        raise ValueError("El email no es válido")

    
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")

    
    usuario_existente = obtener_usuario_por_email(cursor, email)

    if usuario_existente:
        raise ValueError("El email ya está registrado")

    
    # Pendiente: definir el método con el profesor
    password_hash = generate_password_hash(password)

    # Crear el usuario en la base de datos
    id_usuario = crear_usuario(
        cursor,
        nombre,
        apellido,
        email,
        password_hash
    )

    return id_usuario