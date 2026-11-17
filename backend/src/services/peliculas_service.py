import mysql.connector

from backend.db.db import get_connection
from backend.src.repositories.peliculas_repository import obtener_peliculas
from backend.src.validators.duracion_validator import minutos_de_duracion


def listar_peliculas_service(get_connection=None, obtener_peliculas=None):
    conexion = None
    get_connection = get_connection or globals()["get_connection"]
    obtener_peliculas = obtener_peliculas or globals()["obtener_peliculas"]
    try:
        conexion = get_connection()
        with conexion.cursor(dictionary=True, buffered=True) as cursor:
            peliculas = obtener_peliculas(cursor)
        return {"data": {"peliculas": peliculas}, "status": 200}
    except mysql.connector.Error:
        return {"data": {"error": "No se pudieron cargar las películas."}, "status": 500}
    finally:
        if conexion is not None:
            conexion.close()


def crear_pelicula_service(datos, get_connection=None):
    conexion = None
    get_connection = get_connection or globals()["get_connection"]
    try:
        conexion = get_connection()
        with conexion.cursor(dictionary=True, buffered=True) as cursor:
            cursor.execute(
                "SELECT id_pelicula FROM pelicula WHERE titulo = %s",
                (datos["titulo"],),
            )
            if cursor.fetchone():
                return {
                    "data": {"error": "Ya existe una película con ese título"},
                    "status": 409,
                }
            cursor.execute(
                """
                INSERT INTO pelicula
                (titulo, sinopsis, poster, duracion_minutos, clasificacion, genero)
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
            id_pelicula = cursor.lastrowid
        conexion.commit()
        return {
            "data": {"mensaje": "Película creada", "id_pelicula": id_pelicula},
            "status": 201,
        }
    except mysql.connector.Error:
        if conexion is not None:
            conexion.rollback()
        return {"data": {"error": "No se pudo guardar la película"}, "status": 500}
    finally:
        if conexion is not None:
            conexion.close()


def editar_pelicula_service(id_pelicula, datos, get_connection=None):
    conexion = None
    get_connection = get_connection or globals()["get_connection"]
    try:
        conexion = get_connection()
        with conexion.cursor(dictionary=True, buffered=True) as cursor:
            cursor.execute(
                "SELECT id_pelicula FROM pelicula WHERE id_pelicula = %s",
                (id_pelicula,),
            )
            if not cursor.fetchone():
                return {"data": {"error": "Película no encontrada"}, "status": 404}
            cursor.execute(
                """
                UPDATE pelicula
                SET titulo=%s, sinopsis=%s, poster=%s, duracion_minutos=%s,
                    clasificacion=%s, genero=%s
                WHERE id_pelicula=%s
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
        conexion.commit()
        return {
            "data": {"mensaje": "Película actualizada", "id_pelicula": id_pelicula},
            "status": 200,
        }
    except mysql.connector.Error:
        if conexion is not None:
            conexion.rollback()
        return {"data": {"error": "No se pudo actualizar la película"}, "status": 500}
    finally:
        if conexion is not None:
            conexion.close()
