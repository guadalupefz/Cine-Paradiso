from backend.db.db import get_connection

def obtener_usuario_por_email(email):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id_usuario FROM usuario WHERE email = %s", (email,))
            return cursor.fetchone()
    finally:
        conn.close()

def crear_usuario(nombre, apellido, email, password_hash, rol):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO usuario (nombre, apellido, email, password_hash, rol)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (nombre, apellido, email, password_hash, rol))
            id_creado = cursor.lastrowid
        conn.commit()
        return id_creado
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def buscar_credenciales(cursor, email):
    cursor.execute("SELECT id_usuario, nombre, apellido, email, password_hash, rol FROM usuario WHERE email = %s", (email,))
    return cursor.fetchone()

def obtener_perfil(cursor, id_usuario):
    cursor.execute("SELECT id_usuario, nombre, apellido, email, rol FROM usuario WHERE id_usuario = %s", (id_usuario,))
    return cursor.fetchone()
