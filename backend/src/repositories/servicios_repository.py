def obtener_servicios(cursor):
    cursor.execute("""
        SELECT id_servicio, nombre, descripcion, precio, imagen
        FROM servicio_adicional
        ORDER BY nombre
    """)
    return cursor.fetchall()


def obtener_servicio(cursor, id_servicio):
    cursor.execute("""
        SELECT id_servicio, nombre, descripcion, precio, imagen
        FROM servicio_adicional
        WHERE id_servicio = %s
    """, (id_servicio,))
    return cursor.fetchone()


def crear_servicio(cursor, nombre, descripcion, precio, imagen):
    cursor.execute("""
        INSERT INTO servicio_adicional (nombre, descripcion, precio, imagen)
        VALUES (%s, %s, %s, %s)
    """, (nombre, descripcion, precio, imagen))
    return cursor.lastrowid


def modificar_servicio(cursor, id_servicio, nombre, descripcion, precio, imagen):
    if imagen:
        cursor.execute("""
            UPDATE servicio_adicional
            SET nombre = %s, descripcion = %s, precio = %s, imagen = %s
            WHERE id_servicio = %s
        """, (nombre, descripcion, precio, imagen, id_servicio))
    else:
        cursor.execute("""
            UPDATE servicio_adicional
            SET nombre = %s, descripcion = %s, precio = %s
            WHERE id_servicio = %s
        """, (nombre, descripcion, precio, id_servicio))


def eliminar_servicio(cursor, id_servicio):
    cursor.execute("""
        DELETE FROM servicio_adicional
        WHERE id_servicio = %s
    """, (id_servicio,))
    return cursor.rowcount