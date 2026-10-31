def obtener_salas_por_local(cursor, local_id):
    query = "SELECT id_sala, nombre, capacidad FROM sala WHERE id_local = %s"
    cursor.execute(query, (local_id,))
    return cursor.fetchall()