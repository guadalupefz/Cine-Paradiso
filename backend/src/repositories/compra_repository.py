
def obtener_funcion(cursor, id_funcion):
    query = """
        SELECT id_funcion, id_sala, precio_base
        FROM funcion
        WHERE id_funcion = %s
    """
    cursor.execute(query, (id_funcion,))
    return cursor.fetchone()


def obtener_butacas_de_funcion(cursor, id_funcion):
    query = """
        SELECT b.id_butaca
        FROM funcion f
        JOIN butaca b ON b.id_sala = f.id_sala
        WHERE f.id_funcion = %s
    """
    cursor.execute(query, (id_funcion,))
    return cursor.fetchall()


def obtener_butacas_ocupadas(cursor, id_funcion):
    query = """
        SELECT id_butaca
        FROM entrada
        WHERE id_funcion = %s
    """
    cursor.execute(query, (id_funcion,))
    return cursor.fetchall()


def crear_compra(cursor, id_usuario, total, estado):
    query = """
        INSERT INTO compra (id_usuario, total, estado)
        VALUES (%s, %s, %s)
    """
    cursor.execute(query, (id_usuario, total, estado))
    return cursor.lastrowid


def crear_entrada(cursor, id_compra, id_funcion, id_butaca, qr_token):
    query = """
        INSERT INTO entrada (id_compra, id_funcion, id_butaca, qr_token)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (id_compra, id_funcion, id_butaca, qr_token))
    return cursor.lastrowid


def obtener_compra_por_id(cursor, id_compra):
    query = """
        SELECT id_compra, id_usuario, fecha_hora, total, estado
        FROM compra
        WHERE id_compra = %s
    """
    cursor.execute(query, (id_compra,))
    return cursor.fetchone()


def obtener_entradas_por_compra(cursor, id_compra):
    query = """
        SELECT id_entrada, id_funcion, id_butaca, qr_token,
               fecha_hora_validacion
        FROM entrada
        WHERE id_compra = %s
    """
    cursor.execute(query, (id_compra,))
    return cursor.fetchall()
