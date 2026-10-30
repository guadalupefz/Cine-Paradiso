
# Buscar un usuario por su email
def obtener_usuario_por_email(cursor, email):
    query = """
        SELECT id_usuario, nombre, apellido, email, password_hash, rol
        FROM usuario
        WHERE email = %s
    """

    cursor.execute(query, (email,))
    return cursor.fetchone()


# Registrar un nuevo usuario
def crear_usuario(cursor, nombre, apellido, email, password_hash):
    query = """
        INSERT INTO usuario (
            nombre,
            apellido,
            email,
            password_hash,
            rol
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(query, (
        nombre,
        apellido,
        email,
        password_hash,
        "cliente"
    ))

    return cursor.lastrowid