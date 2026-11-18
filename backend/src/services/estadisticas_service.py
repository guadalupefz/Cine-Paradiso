import backend.src.repositories.estadisticas_repository as repo


def consultar_ventas_service(cursor, desde=None, hasta=None, id_local=None):
    por_genero = repo.obtener_ventas_por_genero(
        cursor, desde, hasta, id_local
    )
    por_franja = repo.obtener_ventas_por_franja(
        cursor, desde, hasta, id_local
    )
    cancelaciones = repo.obtener_cantidad_cancelaciones(
        cursor, desde, hasta, id_local
    )

    return {
        "ventas_por_genero": por_genero or [],
        "ventas_por_franja_horaria": por_franja or [],
        "cantidad_cancelaciones": cancelaciones.get("cantidad_cancelaciones", 0),
        "filtros": {
            "desde": desde,
            "hasta": hasta,
            "id_local": id_local
        }
    }


def consultar_ocupacion_service(cursor, desde=None, hasta=None, id_local=None):
    por_funcion = repo.obtener_ocupacion_por_funcion(
        cursor, desde, hasta, id_local
    )
    por_pelicula = repo.obtener_ocupacion_por_pelicula(
        cursor, desde, hasta, id_local
    )

    return {
        "ocupacion_por_funcion": por_funcion or [],
        "ocupacion_por_pelicula": por_pelicula or [],
        "filtros": {
            "desde": desde,
            "hasta": hasta,
            "id_local": id_local
        }
    }
