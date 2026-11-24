"""Consultas de tokens invalidados al cerrar sesión."""


def buscar_token_revocado(cursor, identificador):
    cursor.execute("SELECT jti FROM token_revocado WHERE jti = %s", (identificador,))
    return cursor.fetchone()


def guardar_token_revocado(cursor, identificador, vencimiento):
    cursor.execute(
        "INSERT INTO token_revocado (jti, vence_en) VALUES (%s, %s)",
        (identificador, vencimiento),
    )


def eliminar_tokens_vencidos(cursor):
    cursor.execute("DELETE FROM token_revocado WHERE vence_en <= UTC_TIMESTAMP()")
