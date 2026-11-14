from backend.db.db import get_connection
import backend.src.repositories.estadisticas_repository as repo


def consultar_ventas_service(desde=None, hasta=None):
    conn = get_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            por_genero = repo.obtener_ventas_por_genero(cursor, desde, hasta)
            por_franja = repo.obtener_ventas_por_franja(cursor, desde, hasta)
            
            # repo.obtener_cantidad_cancelaciones devuelve directamente un int
            cant_cancelaciones = repo.obtener_cantidad_cancelaciones(cursor, desde, hasta)

        return {
            "ventas_por_genero": por_genero or [],
            "ventas_por_franja_horaria": por_franja or [],
            "cantidad_cancelaciones": cant_cancelaciones,
            "filtros": {"desde": desde, "hasta": hasta}
        }
    finally:
        if conn and conn.is_connected():
            conn.close()


def consultar_ocupacion_service(desde=None, hasta=None):
    conn = get_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            por_funcion = repo.obtener_ocupacion_por_funcion(cursor, desde, hasta)
            por_pelicula = repo.obtener_ocupacion_por_pelicula(cursor, desde, hasta)

        return {
            "ocupacion_por_funcion": por_funcion or [],
            "ocupacion_por_pelicula": por_pelicula or [],
            "filtros": {"desde": desde, "hasta": hasta}
        }
    finally:
        if conn and conn.is_connected():
            conn.close()