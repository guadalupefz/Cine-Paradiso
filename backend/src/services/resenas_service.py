from backend.src.repositories import resenas_repository as repo


def obtener_resenas_pelicula(cursor, id_pelicula):
    resumen = repo.obtener_resumen_resenas(cursor, id_pelicula)

    if resumen is None:
        return None

    resenas = repo.listar_resenas(cursor, id_pelicula)

    return {
        "pelicula": {
            "id_pelicula": resumen["id_pelicula"],
            "titulo": resumen["titulo"],
        },
        "cantidad": int(resumen["cantidad"]),
        "promedio": float(resumen["promedio"]),
        "resenas": resenas,
    }


def obtener_resena_propia(cursor, id_usuario, id_pelicula):
    return repo.obtener_resena_y_elegibilidad(
        cursor, id_usuario, id_pelicula
    )


def guardar_resena(cursor, id_usuario, id_pelicula, puntuacion, comentario):
    pelicula = repo.obtener_resumen_resenas(cursor, id_pelicula)

    if pelicula is None:
        return None, "PELICULA_NO_ENCONTRADA"

    if not repo.tiene_asistencia_validada(cursor, id_usuario, id_pelicula):
        return None, "ASISTENCIA_NO_VALIDADA"

    repo.guardar_resena(
        cursor, id_usuario, id_pelicula, puntuacion, comentario
    )

    return {"mensaje": "La reseña se guardó correctamente."}, None
