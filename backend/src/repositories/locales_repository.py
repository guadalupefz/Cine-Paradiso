def obtener_locales(cursor):
    query = "SELECT id_local, nombre, direccion FROM local"
    cursor.execute(query)
    return cursor.fetchall()


def bloquear_local(cursor, id_local):
    cursor.execute("SELECT id_local FROM local WHERE id_local = %s FOR UPDATE", (id_local,))
    return cursor.fetchone()


def bloquear_salas_del_local(cursor, id_local):
    cursor.execute("SELECT id_sala FROM sala WHERE id_local = %s ORDER BY id_sala FOR UPDATE", (id_local,))
    cursor.fetchall()


def local_en_uso(cursor, id_local):
    cursor.execute(
        """SELECT EXISTS(SELECT 1 FROM funcion f
                            JOIN sala s ON s.id_sala = f.id_sala
                            WHERE s.id_local = %s)
                  OR EXISTS(SELECT 1 FROM entrada e
                            JOIN butaca b ON b.id_butaca = e.id_butaca
                            JOIN sala s ON s.id_sala = b.id_sala
                            WHERE s.id_local = %s) AS en_uso""",
        (id_local, id_local),
    )
    return bool(cursor.fetchone()["en_uso"])


def eliminar_local_salas_y_butacas(cursor, id_local):
    cursor.execute(
        "DELETE b FROM butaca b JOIN sala s ON s.id_sala = b.id_sala WHERE s.id_local = %s",
        (id_local,),
    )
    cursor.execute("DELETE FROM sala WHERE id_local = %s", (id_local,))
    cursor.execute("DELETE FROM local WHERE id_local = %s", (id_local,))
    return cursor.rowcount
