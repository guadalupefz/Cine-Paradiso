from backend.db.db import get_connection


def obtener_usuario_por_email(email):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id_usuario FROM usuario WHERE email = %s",
            (email,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def crear_usuario(nombre, apellido, email, password_hash, rol):
    conn = get_connection()
    try:
        cursor = conn.cursor()

        query = """
            INSERT INTO usuario (nombre, apellido, email, password_hash, rol)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(query, (nombre, apellido, email, password_hash, rol))
        id_creado = cursor.lastrowid

        conn.commit()
        return id_creado

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def buscar_credenciales(email):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id_usuario, nombre, apellido, email, password_hash, rol
            FROM usuario
            WHERE email = %s
            """,
            (email,)
        )

        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def obtener_perfil(id_usuario):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id_usuario, nombre, apellido, email, rol
            FROM usuario
            WHERE id_usuario = %s
            """,
            (id_usuario,)
        )

        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
