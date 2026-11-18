from backend.src.repositories.peliculas_repository import (
    buscar_pelicula_por_id,
    buscar_pelicula_por_titulo,
    crear_pelicula,
    editar_pelicula,
    obtener_funcion_de_pelicula,
    obtener_peliculas,
)
from backend.src.validators.duracion_validator import minutos_de_duracion


def listar_peliculas_service(cursor):
    return {"data": {"peliculas": obtener_peliculas(cursor)}, "status": 200}


def crear_pelicula_service(cursor, datos):
    if buscar_pelicula_por_titulo(cursor, datos["titulo"]):
        return {
            "data": {"error": "Ya existe una película con ese título"},
            "status": 409,
        }

    id_pelicula = crear_pelicula(cursor, datos)
    return {
        "data": {"mensaje": "Película creada", "id_pelicula": id_pelicula},
        "status": 201,
    }


def editar_pelicula_service(cursor, id_pelicula, datos):
    pelicula = buscar_pelicula_por_id(cursor, id_pelicula)
    if not pelicula:
        return {"data": {"error": "Película no encontrada"}, "status": 404}

    duplicada = buscar_pelicula_por_titulo(cursor, datos["titulo"])
    if duplicada and duplicada["id_pelicula"] != id_pelicula:
        return {
            "data": {"error": "Ya existe una película con ese título"},
            "status": 409,
        }

    try:
        duracion_actual = minutos_de_duracion(pelicula["duracion_minutos"])
    except ValueError:
        duracion_actual = None

    if duracion_actual != datos["duracion_minutos"]:
        if obtener_funcion_de_pelicula(cursor, id_pelicula):
            return {
                "data": {
                    "error": (
                        "No se puede cambiar la duración de una película "
                        "con funciones programadas."
                    )
                },
                "status": 409,
            }

    editar_pelicula(cursor, id_pelicula, datos)
    return {
        "data": {
            "mensaje": "Película actualizada",
            "id_pelicula": id_pelicula,
        },
        "status": 200,
    }
