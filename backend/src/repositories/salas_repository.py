def obtener_salas_por_local(cursor, local_id):
    query = "SELECT id_sala, nombre, capacidad FROM sala WHERE id_local = %s"
    cursor.execute(query, (local_id,))
    return cursor.fetchall()


def bloquear_sala(cursor, id_sala):
    cursor.execute("SELECT id_sala FROM sala WHERE id_sala = %s FOR UPDATE", (id_sala,))
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
