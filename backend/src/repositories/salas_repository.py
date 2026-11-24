def obtener_salas_por_local(cursor, id_local):
    query = "SELECT id_sala, nombre, capacidad FROM sala WHERE id_local = %s"
    cursor.execute(query, (id_local,))
    return cursor.fetchall()


def existe_local(cursor, id_local):
    cursor.execute(
        "SELECT id_local FROM local WHERE id_local = %s",
        (id_local,)
    )
    return cursor.fetchone() is not None


def crear_sala(cursor, id_local, nombre, capacidad):
    query = """
        INSERT INTO sala (id_local, nombre, capacidad)
        VALUES (%s, %s, %s)
    """
    cursor.execute(query, (id_local, nombre, capacidad))
    return cursor.lastrowid


def bloquear_sala(cursor, id_sala):
    cursor.execute(
        "SELECT id_sala, capacidad FROM sala WHERE id_sala = %s FOR UPDATE",
        (id_sala,)
    )
    return cursor.fetchone()


def sala_en_uso(cursor, id_sala):
    cursor.execute(
        """SELECT EXISTS(SELECT 1 FROM funcion WHERE id_sala = %s)
                  OR EXISTS(SELECT 1 FROM entrada e
                            JOIN butaca b ON b.id_butaca = e.id_butaca
                            WHERE b.id_sala = %s) AS en_uso""",
        (id_sala, id_sala),
    )
    return bool(cursor.fetchone()["en_uso"])


def eliminar_sala_y_butacas(cursor, id_sala):
    cursor.execute("DELETE FROM butaca WHERE id_sala = %s", (id_sala,))
    cursor.execute("DELETE FROM sala WHERE id_sala = %s", (id_sala,))
    return cursor.rowcount