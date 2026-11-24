def obtener_cartelera(cursor):
    query = """
        SELECT p.id_pelicula, p.titulo, p.sinopsis, p.poster,
               p.duracion_minutos, p.clasificacion, p.genero,
               f.id_funcion, f.fecha_hora_inicio, f.precio_base,
               s.id_sala, s.nombre AS sala_nombre, s.capacidad,
               l.nombre AS local_nombre
        FROM funcion f
        JOIN pelicula p ON f.id_pelicula = p.id_pelicula
        JOIN sala s ON f.id_sala = s.id_sala
        JOIN local l ON s.id_local = l.id_local
        WHERE f.fecha_hora_inicio > NOW()
    """
    cursor.execute(query)
    return cursor.fetchall()


def obtener_funciones(cursor, solo_vigentes=False):
    query = """
        SELECT f.id_funcion, f.id_pelicula, f.id_sala,
               f.fecha_hora_inicio, f.precio_base,
               p.titulo, s.nombre AS sala_nombre
        FROM funcion f
        JOIN pelicula p ON f.id_pelicula = p.id_pelicula
        JOIN sala s ON f.id_sala = s.id_sala
    """
    if solo_vigentes:
        query += " WHERE f.fecha_hora_inicio > NOW()"
    cursor.execute(query)
    return cursor.fetchall()


def crear_funcion(cursor, id_pelicula, id_sala, fecha_hora_inicio, precio_base):
    query = """
        INSERT INTO funcion
        (id_pelicula, id_sala, fecha_hora_inicio, precio_base)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (id_pelicula, id_sala, fecha_hora_inicio, precio_base))
    return cursor.lastrowid


def modificar_funcion(cursor, funcion_id, id_pelicula, id_sala, fecha_hora_inicio, precio_base):
    query = """
        UPDATE funcion
        SET id_pelicula = %s, id_sala = %s,
            fecha_hora_inicio = %s, precio_base = %s
        WHERE id_funcion = %s
    """
    cursor.execute(query, (id_pelicula, id_sala, fecha_hora_inicio, precio_base, funcion_id))
    return cursor.rowcount


def contar_entradas_por_funcion(cursor, id_funcion):
    query = "SELECT COUNT(*) AS total FROM entrada WHERE id_funcion = %s"
    cursor.execute(query, (id_funcion,))
    resultado = cursor.fetchone()
    return resultado["total"] if isinstance(resultado, dict) else resultado[0]


def obtener_funciones_por_sala(cursor, id_sala, id_funcion_excluir=None):
    query = """
        SELECT f.id_funcion, f.fecha_hora_inicio, p.duracion_minutos
        FROM funcion f
        JOIN pelicula p ON f.id_pelicula = p.id_pelicula
        WHERE f.id_sala = %s
    """
    parametros = [id_sala]

    if id_funcion_excluir is not None:
        query += " AND f.id_funcion != %s"
        parametros.append(id_funcion_excluir)

    cursor.execute(query, tuple(parametros))
    return cursor.fetchall()


def obtener_funcion_por_id(cursor, id_funcion):
    query = """
        SELECT id_funcion, id_pelicula, id_sala, fecha_hora_inicio
        FROM funcion
        WHERE id_funcion = %s
    """
    cursor.execute(query, (id_funcion,))
    return cursor.fetchone()


def obtener_pelicula_por_id(cursor, id_pelicula):
    query = """
        SELECT id_pelicula, duracion_minutos
        FROM pelicula
        WHERE id_pelicula = %s
    """
    cursor.execute(query, (id_pelicula,))
    return cursor.fetchone()


def obtener_sala_por_id(cursor, id_sala):
    query = """
        SELECT id_sala
        FROM sala
        WHERE id_sala = %s
    """
    cursor.execute(query, (id_sala,))
    return cursor.fetchone()


def existe_funcion(cursor, id_funcion):
    query = "SELECT id_funcion FROM funcion WHERE id_funcion = %s"
    cursor.execute(query, (id_funcion,))
    return cursor.fetchone() is not None