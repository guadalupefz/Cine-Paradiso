def obtener_servicios(cursor):
    cursor.execute("SELECT id_servicio, nombre, precio FROM servicio_adicional ORDER BY nombre")
    return cursor.fetchall()

def obtener_servicio(cursor, id_servicio):
    cursor.execute("SELECT id_servicio, nombre, precio FROM servicio_adicional WHERE id_servicio = %s", (id_servicio,))
    return cursor.fetchone()

def crear_servicio(cursor, nombre, precio):
    cursor.execute("INSERT INTO servicio_adicional (nombre, precio) VALUES (%s, %s)", (nombre, precio))
    return cursor.lastrowid

def modificar_servicio(cursor, id_servicio, nombre, precio):
    cursor.execute("UPDATE servicio_adicional SET nombre = %s, precio = %s WHERE id_servicio = %s", (nombre, precio, id_servicio))

def eliminar_servicio(cursor, id_servicio):
    cursor.execute("DELETE FROM servicio_adicional WHERE id_servicio = %s", (id_servicio,))
    return cursor.rowcount
