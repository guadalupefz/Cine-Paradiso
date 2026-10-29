# Obtener todos los locales
def obtener_locales(cursor):
    query = "SELECT id_local, nombre, direccion FROM local"
    cursor.execute(query)
    return cursor.fetchall()


# Obtener las salas pertenecientes a un local específico
def obtener_salas_por_local(cursor, local_id):
    query = "SELECT id_sala, nombre, capacidad FROM sala WHERE id_local = %s"
    cursor.execute(query, (local_id,))
    return cursor.fetchall()


# Obtener el catálogo completo de películas
def obtener_peliculas(cursor):
    query = "SELECT id_pelicula, titulo, sinopsis, poster, duracion_minutos, clasificacion, genero FROM pelicula"
    cursor.execute(query)
    return cursor.fetchall()


# Consultar la cartelera vigente cruzando películas, salas, locales y fechas futuras
def obtener_cartelera(cursor):
    query = """
        SELECT p.id_pelicula, p.titulo, p.sinopsis, p.poster, p.duracion_minutos, p.clasificacion, p.genero,
               f.id_funcion, f.fecha_hora_inicio, f.precio_base, s.id_sala, s.nombre as sala_nombre, l.nombre as local_nombre
        FROM funcion f
        JOIN pelicula p ON f.id_pelicula = p.id_pelicula
        JOIN sala s ON f.id_sala = s.id_sala
        JOIN local l ON s.id_local = l.id_local
        WHERE f.fecha_hora_inicio >= NOW()
    """
    cursor.execute(query)
    return cursor.fetchall()


# Listar todas las funciones disponibles
def obtener_funciones(cursor):
    query = """
        SELECT f.id_funcion, f.fecha_hora_inicio, f.precio_base, p.titulo, s.nombre as sala_nombre
        FROM funcion f
        JOIN pelicula p ON f.id_pelicula = p.id_pelicula
        JOIN sala s ON f.id_sala = s.id_sala
    """
    cursor.execute(query)
    return cursor.fetchall()


# Crear una nueva función (Administrador)
def crear_funcion(cursor, id_pelicula, id_sala, fecha_hora_inicio, precio_base):
    query = "INSERT INTO funcion (id_pelicula, id_sala, fecha_hora_inicio, precio_base) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (id_pelicula, id_sala, fecha_hora_inicio, precio_base))
    return cursor.lastrowid   #Devuelve el ultimo id creado


# Modificar una función existente (Administrador)
def modificar_funcion(cursor, funcion_id, id_pelicula, id_sala, fecha_hora_inicio, precio_base):
    query = """
        UPDATE funcion 
        SET id_pelicula = %s, id_sala = %s, fecha_hora_inicio = %s, precio_base = %s
        WHERE id_funcion = %s
    """
    cursor.execute(query, (id_pelicula, id_sala, fecha_hora_inicio, precio_base, funcion_id))
    return cursor.rowcount   #Devuelve la cantidad de filas modificadas


# Sincronizar películas con una API externa
def sincronizar_pelicula(cursor, pelicula):
    query = """
        INSERT INTO pelicula (titulo, sinopsis, poster, duracion_minutos, clasificacion, genero)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (
        pelicula["titulo"],
        pelicula["sinopsis"],
        pelicula["poster"],
        pelicula["duracion_minutos"],
        pelicula["clasificacion"],
        pelicula["genero"]
    ))


# Obtener las butacas de una función y su estado de ocupación
def obtener_butacas_por_funcion(cursor, id_funcion):
    query = """
        SELECT
            b.id_butaca,
            b.fila,
            b.numero,
            CASE
                WHEN e.id_entrada IS NOT NULL THEN 'ocupada'
                ELSE 'disponible'
            END AS estado
        FROM funcion f
        JOIN sala s ON f.id_sala = s.id_sala
        JOIN butaca b ON s.id_sala = b.id_sala
        LEFT JOIN entrada e
            ON e.id_funcion = f.id_funcion
            AND e.id_butaca = b.id_butaca
        WHERE f.id_funcion = %s
        ORDER BY b.fila, b.numero
    """
    cursor.execute(query, (id_funcion,))
    return cursor.fetchall()
