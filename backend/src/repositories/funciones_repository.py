# Consultar la cartelera vigente
def obtener_cartelera(cursor):
    query = """
        SELECT p.id_pelicula, p.titulo, p.sinopsis, p.poster,
               p.duracion_minutos, p.clasificacion, p.genero,
               f.id_funcion, f.fecha_hora_inicio, f.precio_base,
               s.id_sala, s.nombre AS sala_nombre,
               l.nombre AS local_nombre
        FROM funcion f
        JOIN pelicula p ON f.id_pelicula = p.id_pelicula
        JOIN sala s ON f.id_sala = s.id_sala
        JOIN local l ON s.id_local = l.id_local
        WHERE f.fecha_hora_inicio >= NOW()
    """
    cursor.execute(query)
    return cursor.fetchall()


# Listar todas las funciones
def obtener_funciones(cursor):
    query = """
        SELECT f.id_funcion, f.fecha_hora_inicio, f.precio_base,
               p.titulo, s.nombre AS sala_nombre
        FROM funcion f
        JOIN pelicula p ON f.id_pelicula = p.id_pelicula
        JOIN sala s ON f.id_sala = s.id_sala
    """
    cursor.execute(query)
    return cursor.fetchall()


# Crear una nueva función
def crear_funcion(cursor, id_pelicula, id_sala, fecha_hora_inicio, precio_base):
    query = """
        INSERT INTO funcion (id_pelicula, id_sala, fecha_hora_inicio, precio_base)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (id_pelicula, id_sala, fecha_hora_inicio, precio_base))
    return cursor.lastrowid


# Modificar una función existente
def modificar_funcion(cursor, funcion_id, id_pelicula, id_sala, fecha_hora_inicio, precio_base):
    query = """
        UPDATE funcion
        SET id_pelicula = %s, id_sala = %s,
            fecha_hora_inicio = %s, precio_base = %s
        WHERE id_funcion = %s
    """
    cursor.execute(query, (id_pelicula, id_sala, fecha_hora_inicio, precio_base, funcion_id))
    return cursor.rowcount