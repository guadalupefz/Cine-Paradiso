import mysql.connector
from typing import cast

from backend.db.db import get_connection

def obtener_peliculas():
    conexion = None

    try:
        conexion = get_connection()

        with conexion.cursor(dictionary=True, buffered=True) as cursor:
            cursor.execute("""
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
            """)

            return cursor.fetchall()

    finally:
        if conexion is not None:
            conexion.close()


def buscar_pelicula_por_titulo(titulo):
    conexion = None

    try:
        conexion = get_connection()

        with conexion.cursor(dictionary=True, buffered=True) as cursor:
            cursor.execute("""
                SELECT id_pelicula, titulo
                FROM pelicula
                WHERE titulo = %s
            """, (titulo,))

            return cursor.fetchone()

    finally:
        if conexion is not None:
            conexion.close()


def buscar_pelicula_por_id_externo(imdb_id):
    conexion = None

    try:
        conexion = get_connection()

        with conexion.cursor(dictionary=True, buffered=True) as cursor:
            cursor.execute("""
                SELECT id_pelicula, id_externo_api, titulo
                FROM pelicula
                WHERE id_externo_api = %s
            """, (imdb_id,))

            return cursor.fetchone()

    finally:
        if conexion is not None:
            conexion.close()


def crear_pelicula(datos):
    conexion = None

    try:
        conexion = get_connection()

        with conexion.cursor() as cursor:
            cursor.execute("""
                INSERT INTO pelicula (
                    titulo,
                    sinopsis,
                    poster,
                    duracion_minutos,
                    clasificacion,
                    genero
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                datos["titulo"],
                datos["sinopsis"],
                datos["poster"],
                datos["duracion_minutos"],
                datos["clasificacion"],
                datos["genero"]
            ))

            id_pelicula = cursor.lastrowid

        conexion.commit()
        return id_pelicula

    except Exception:
        if conexion is not None:
            conexion.rollback()
        raise

    finally:
        if conexion is not None:
            conexion.close()


def editar_pelicula(id_pelicula, datos):
    conexion = None

    try:
        conexion = get_connection()

        with conexion.cursor() as cursor:
            cursor.execute("""
                SELECT id_pelicula
                FROM pelicula
                WHERE id_pelicula = %s
            """, (id_pelicula,))

            if not cursor.fetchone():
                return False

            cursor.execute("""
                SELECT id_pelicula
                FROM pelicula
                WHERE titulo = %s
                  AND id_pelicula != %s
            """, (datos["titulo"], id_pelicula))

            if cursor.fetchone():
                return None

            cursor.execute("""
                UPDATE pelicula
                SET
                    titulo = %s,
                    sinopsis = %s,
                    poster = %s,
                    duracion_minutos = %s,
                    clasificacion = %s,
                    genero = %s
                WHERE id_pelicula = %s
            """, (
                datos["titulo"],
                datos["sinopsis"],
                datos["poster"],
                datos["duracion_minutos"],
                datos["clasificacion"],
                datos["genero"],
                id_pelicula
            ))

        conexion.commit()
        return True

    except Exception:
        if conexion is not None:
            conexion.rollback()
        raise

    finally:
        if conexion is not None:
            conexion.close()


def sincronizar_pelicula(pelicula):
    conexion = None

    try:
        conexion = get_connection()
        with conexion.cursor() as cursor:
            cursor.execute("""
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
            """, (
                pelicula["id_externo_api"],
                pelicula["titulo"],
                pelicula["sinopsis"],
                pelicula["poster"],
                pelicula["duracion_minutos"],
                pelicula["clasificacion"],
                pelicula["genero"]
            ))

            id_pelicula = cursor.lastrowid

        conexion.commit()
        return id_pelicula

    except Exception:
        if conexion is not None:
            conexion.rollback()
        raise

    finally:
        if conexion is not None:
            conexion.close()


def guardar_pelicula(pelicula):
    id_externo_api = pelicula.get("id_externo_api")
    if not id_externo_api:
        return {
            "exito": False,
            "error": "OMDb no devolvió imdbID",
        }

    conexion = None
    try:
        conexion = get_connection()
        with conexion.cursor(dictionary=True) as cursor:
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
                pelicula_existente = cast(
                    dict[str, int], pelicula_existente
                )
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
                id_pelicula = pelicula_existente["id_pelicula"]
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

        conexion.commit()
        return {
            "exito": True,
            "id": id_pelicula,
            "accion": accion,
        }
    except mysql.connector.Error:
        if conexion is not None:
            conexion.rollback()
        return {
            "exito": False,
            "error": "No se pudo guardar la película",
        }
    finally:
        if conexion is not None:
            conexion.close()
