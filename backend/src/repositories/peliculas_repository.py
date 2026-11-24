def obtener_peliculas(cursor):
    cursor.execute(
        """
        SELECT
            id_pelicula,
            id_externo_api,
            titulo,
            sinopsis,
            poster,
            duracion_minutos,
            clasificacion,
            genero
        FROM pelicula
        ORDER BY titulo ASC
        """
    )
    return cursor.fetchall()


def buscar_pelicula_por_titulo(cursor, titulo):
    cursor.execute(
        """
        SELECT id_pelicula, titulo
        FROM pelicula
        WHERE LOWER(titulo) = LOWER(%s)        """,
        (titulo,),
    )
    return cursor.fetchone()


def buscar_pelicula_por_id(cursor, id_pelicula):
    cursor.execute(
        """
        SELECT id_pelicula, duracion_minutos
        FROM pelicula
        WHERE id_pelicula = %s
        """,
        (id_pelicula,),
    )
    return cursor.fetchone()


def obtener_funcion_de_pelicula(cursor, id_pelicula):
    cursor.execute(
        """
        SELECT id_funcion
        FROM funcion
        WHERE id_pelicula = %s
        LIMIT 1
        """,
        (id_pelicula,),
    )
    return cursor.fetchone()


def buscar_pelicula_por_id_externo(cursor, imdb_id):
    cursor.execute(
        """
        SELECT id_pelicula, id_externo_api, titulo
        FROM pelicula
        WHERE id_externo_api = %s
        """,
        (imdb_id,),
    )
    return cursor.fetchone()


def crear_pelicula(cursor, datos):
    cursor.execute(
        """
        INSERT INTO pelicula (
            titulo,
            sinopsis,
            poster,
            duracion_minutos,
            clasificacion,
            genero
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            datos["titulo"],
            datos["sinopsis"],
            datos["poster"],
            datos["duracion_minutos"],
            datos["clasificacion"],
            datos["genero"],
        ),
    )
    return cursor.lastrowid


def editar_pelicula(cursor, id_pelicula, datos):
    cursor.execute(
        """
        UPDATE pelicula
        SET
            titulo = %s,
            sinopsis = %s,
            poster = %s,
            duracion_minutos = %s,
            clasificacion = %s,
            genero = %s
        WHERE id_pelicula = %s
        """,
        (
            datos["titulo"],
            datos["sinopsis"],
            datos["poster"],
            datos["duracion_minutos"],
            datos["clasificacion"],
            datos["genero"],
            id_pelicula,
        ),
    )


def sincronizar_pelicula(cursor, pelicula):
    cursor.execute(
        """
        INSERT INTO pelicula (
            id_externo_api,
            titulo,
            sinopsis,
            poster,
            duracion_minutos,
            clasificacion,
            genero
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            pelicula["id_externo_api"],
            pelicula["titulo"],
            pelicula["sinopsis"],
            pelicula["poster"],
            pelicula["duracion_minutos"],
            pelicula["clasificacion"],
            pelicula["genero"],
        ),
    )
    return cursor.lastrowid


def guardar_pelicula(cursor, pelicula):
    id_externo_api = pelicula.get("id_externo_api")
    if not id_externo_api:
        return {
            "exito": False,
            "error": "OMDb no devolvió imdbID",
        }

    cursor.execute(
        """
        SELECT id_pelicula
        FROM pelicula
        WHERE id_externo_api = %s
        """,
        (id_externo_api,),
    )
    pelicula_existente = cursor.fetchone()

    if pelicula_existente:
        id_pelicula = pelicula_existente["id_pelicula"]
        cursor.execute(
            """
            UPDATE pelicula
            SET titulo = %s,
                sinopsis = %s,
                poster = %s,
                duracion_minutos = %s,
                clasificacion = %s,
                genero = %s
            WHERE id_externo_api = %s
            """,
            (
                pelicula["titulo"],
                pelicula["sinopsis"],
                pelicula["poster"],
                pelicula["duracion_minutos"],
                pelicula["clasificacion"],
                pelicula["genero"],
                id_externo_api,
            ),
        )
        accion = "actualizada"
    else:
        cursor.execute(
            """
            INSERT INTO pelicula (
                id_externo_api,
                titulo,
                sinopsis,
                poster,
                duracion_minutos,
                clasificacion,
                genero
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                id_externo_api,
                pelicula["titulo"],
                pelicula["sinopsis"],
                pelicula["poster"],
                pelicula["duracion_minutos"],
                pelicula["clasificacion"],
                pelicula["genero"],
            ),
        )
        id_pelicula = cursor.lastrowid
        accion = "insertada"

    return {
        "exito": True,
        "id": id_pelicula,
        "accion": accion,
    }
