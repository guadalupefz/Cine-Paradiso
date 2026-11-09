import mysql.connector
from backend.db.db import get_connection


def buscar_pelicula_por_id_externo(cursor, id_externo_api):
    cursor.execute(
        "SELECT id_pelicula FROM pelicula WHERE id_externo_api = %s",
        (id_externo_api,),
    )
    return cursor.fetchone()


def guardar_pelicula(datos):
    """Inserta o actualiza una película identificada por su imdbID."""
    id_externo_api = datos.get("id_externo_api")
    if not isinstance(id_externo_api, str) or not id_externo_api.strip():
        return {"exito": False, "error": "OMDb no devolvió imdbID", "accion": None}

    id_externo_api = id_externo_api.strip()
    conexion = None
    try:
        conexion = get_connection()
        with conexion.cursor(dictionary=True, buffered=True) as cursor:
            cursor.execute(
                "SELECT id_pelicula FROM pelicula WHERE id_externo_api = %s FOR UPDATE",
                (id_externo_api,),
            )
            existente = cursor.fetchone()

            valores = (
                datos["titulo"],
                datos["sinopsis"],
                datos["poster"],
                datos["duracion_minutos"],
                datos["clasificacion"],
                datos["genero"],
            )

            if existente:
                cursor.execute(
                    """
                    UPDATE pelicula
                    SET titulo=%s, sinopsis=%s, poster=%s, duracion_minutos=%s,
                        clasificacion=%s, genero=%s
                    WHERE id_externo_api=%s
                    """,
                    valores + (id_externo_api,),
                )
                accion = "actualizada"
                id_pelicula = existente["id_pelicula"]
            else:
                cursor.execute(
                    """
                    INSERT INTO pelicula
                    (id_externo_api, titulo, sinopsis, poster, duracion_minutos, clasificacion, genero)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (id_externo_api,) + valores,
                )
                accion = "insertada"
                id_pelicula = cursor.lastrowid

        conexion.commit()
        return {"exito": True, "accion": accion, "id": id_pelicula}
    except (mysql.connector.Error, KeyError):
        if conexion is not None:
            conexion.rollback()
        return {"exito": False, "error": "No se pudo guardar la película", "accion": None}
    finally:
        if conexion is not None:
            conexion.close()




