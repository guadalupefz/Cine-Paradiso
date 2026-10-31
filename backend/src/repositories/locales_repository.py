def obtener_locales(cursor):
    query = "SELECT id_local, nombre, direccion FROM local"
    cursor.execute(query)
    return cursor.fetchall()