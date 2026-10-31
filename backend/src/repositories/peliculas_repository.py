# Obtener el catálogo completo de películas
def obtener_peliculas(cursor):
    query = """
        SELECT id_pelicula, titulo, sinopsis, poster,
               duracion_minutos, clasificacion, genero
        FROM pelicula
    """
    cursor.execute(query)
    return cursor.fetchall()


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