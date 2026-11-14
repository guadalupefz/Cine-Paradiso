
def obtener_usuario_por_email(cursor, email):
    query = """
        SELECT id_usuario
        FROM usuario
        WHERE email = %s
    """
    cursor.execute(query, (email,))
    return cursor.fetchone()


def crear_usuario(cursor, nombre, apellido, email, password_hash, rol):
    query = """
        INSERT INTO usuario (nombre, apellido, email, password_hash, rol)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (nombre, apellido, email, password_hash, rol))
    return cursor.lastrowid


def buscar_credenciales(cursor, email):
    query = """
        SELECT id_usuario, nombre, apellido, email, password_hash, rol
        FROM usuario
        WHERE email = %s
    """
    cursor.execute(query, (email,))
    return cursor.fetchone()


def obtener_perfil(cursor, id_usuario):
    query = """
        SELECT id_usuario, nombre, apellido, email, rol
        FROM usuario
        WHERE id_usuario = %s
    """
    cursor.execute(query, (id_usuario,))
    return cursor.fetchone()