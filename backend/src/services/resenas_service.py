from typing import TypedDict

from backend.db.db import get_connection
from backend.src.repositories import resenas_repository as repo


class ResumenPeliculaResenas(TypedDict):
    pelicula: dict[str, int | str]
    cantidad: int
    promedio: float
    resenas: list[repo.ResenaPublica]


def obtener_resenas_pelicula(id_pelicula: int) -> ResumenPeliculaResenas | None:
    conexion = get_connection()
    try:
        with conexion.cursor(dictionary=True) as cursor:
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
    finally:
        conexion.close()


def obtener_resena_propia(
    id_usuario: int, id_pelicula: int
) -> repo.ResenaPropia | None:
    conexion = get_connection()
    try:
        with conexion.cursor(dictionary=True) as cursor:
            resena = repo.obtener_resena_y_elegibilidad(
                cursor, id_usuario, id_pelicula
            )
        return resena
    finally:
        conexion.close()


def guardar_resena(
    id_usuario: int,
    id_pelicula: int,
    puntuacion: int,
    comentario: str,
) -> tuple[dict[str, str] | None, str | None, int]:
    conexion = get_connection()
    try:
        conexion.start_transaction()
        with conexion.cursor(dictionary=True) as cursor:
            pelicula = repo.obtener_resumen_resenas(cursor, id_pelicula)
            if pelicula is None:
                conexion.rollback()
                return None, "No se encontró la película.", 404

            if not repo.tiene_asistencia_validada(
                cursor, id_usuario, id_pelicula
            ):
                conexion.rollback()
                return (
                    None,
                    "Solo podés reseñar películas de entradas validadas por QR.",
                    403,
                )

            repo.guardar_resena(
                cursor, id_usuario, id_pelicula, puntuacion, comentario
            )

        conexion.commit()
        return {"mensaje": "La reseña se guardó correctamente."}, None, 200
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()
