from datetime import datetime
from decimal import Decimal
from typing import TypedDict, cast


class ResumenResenas(TypedDict):
    id_pelicula: int
    titulo: str
    cantidad: int
    promedio: Decimal | float | int


class ResenaPublica(TypedDict):
    puntuacion: int
    comentario: str
    fecha_actualizacion: datetime


class ResenaPropia(TypedDict):
    puede_resenar: bool | int
    puntuacion: int | None
    comentario: str | None
    fecha_actualizacion: datetime | None


def obtener_resumen_resenas(cursor, id_pelicula):
    cursor.execute(
        """
        SELECT p.id_pelicula, p.titulo,
               COUNT(r.id_resena) AS cantidad,
               COALESCE(AVG(r.puntuacion), 0) AS promedio
        FROM pelicula p
        LEFT JOIN resena r ON r.id_pelicula = p.id_pelicula
        WHERE p.id_pelicula = %s
        GROUP BY p.id_pelicula, p.titulo
        """,
        (id_pelicula,),
    )
    return cast(ResumenResenas | None, cursor.fetchone())


def listar_resenas(cursor, id_pelicula):
    cursor.execute(
        """
        SELECT puntuacion, comentario, fecha_actualizacion
        FROM resena
        WHERE id_pelicula = %s
        ORDER BY fecha_actualizacion DESC, id_resena DESC
        """,
        (id_pelicula,),
    )
    return cast(list[ResenaPublica] | None, cursor.fetchall()) or []


def obtener_resena_y_elegibilidad(cursor, id_usuario, id_pelicula):
    cursor.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM entrada e
            JOIN compra c ON c.id_compra = e.id_compra
            JOIN funcion f ON f.id_funcion = e.id_funcion
            WHERE c.id_usuario = %s
              AND c.estado = 'confirmada'
              AND f.id_pelicula = %s
              AND e.fecha_hora_validacion IS NOT NULL
        ) AS puede_resenar,
        r.puntuacion, r.comentario, r.fecha_actualizacion
        FROM pelicula p
        LEFT JOIN resena r
            ON r.id_pelicula = p.id_pelicula
           AND r.id_usuario = %s
        WHERE p.id_pelicula = %s
        """,
        (id_usuario, id_pelicula, id_usuario, id_pelicula),
    )
    return cast(ResenaPropia | None, cursor.fetchone())


def tiene_asistencia_validada(cursor, id_usuario, id_pelicula):
    cursor.execute(
        """
        SELECT 1
        FROM entrada e
        JOIN compra c ON c.id_compra = e.id_compra
        JOIN funcion f ON f.id_funcion = e.id_funcion
        WHERE c.id_usuario = %s
          AND c.estado = 'confirmada'
          AND f.id_pelicula = %s
          AND e.fecha_hora_validacion IS NOT NULL
        LIMIT 1
        FOR UPDATE
        """,
        (id_usuario, id_pelicula),
    )
    return cursor.fetchone() is not None


def guardar_resena(cursor, id_usuario, id_pelicula, puntuacion, comentario):
    cursor.execute(
        """
        INSERT INTO resena (id_usuario, id_pelicula, puntuacion, comentario)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            puntuacion = VALUES(puntuacion),
            comentario = VALUES(comentario),
            fecha_actualizacion = CURRENT_TIMESTAMP
        """,
        (id_usuario, id_pelicula, puntuacion, comentario),
    )
