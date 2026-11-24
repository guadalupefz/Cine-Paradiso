from datetime import datetime, timedelta

from backend.src.validators.duracion_validator import minutos_de_duracion
from backend.src.repositories.funciones_repository import (
    obtener_funciones,
    obtener_cartelera,
    obtener_funciones_por_sala,
    obtener_funcion_por_id,
    obtener_pelicula_por_id,
    obtener_sala_por_id,
    crear_funcion,
    modificar_funcion,
    contar_entradas_por_funcion,
)


def listar_funciones_servicio(cursor, solo_vigentes=False):
    return obtener_funciones(cursor, solo_vigentes=solo_vigentes)


def consultar_cartelera_servicio(cursor):
    return obtener_cartelera(cursor)


def validar_duracion_pelicula(pelicula):
    if not pelicula:
        raise ValueError("La película especificada no existe.")

    try:
        duracion = minutos_de_duracion(pelicula["duracion_minutos"])
    except (TypeError, ValueError) as error:
        raise ValueError("La duración de la película no es válida.") from error

    if duracion <= 0:
        raise ValueError("La duración de la película debe ser positiva.")

    return duracion


def verificar_solapamiento_servicio(
    cursor, id_sala, fecha_hora_inicio, duracion_minutos,
    id_funcion_excluir=None
):
    if isinstance(fecha_hora_inicio, str):
        inicio_nueva = datetime.fromisoformat(
            fecha_hora_inicio.replace(" ", "T")
        )
    else:
        inicio_nueva = fecha_hora_inicio

    fin_nueva = inicio_nueva + timedelta(minutes=duracion_minutos)

    funciones_existentes = obtener_funciones_por_sala(
        cursor, id_sala, id_funcion_excluir
    )

    for funcion in funciones_existentes:
        inicio_existente = funcion["fecha_hora_inicio"]

        try:
            duracion_existente = minutos_de_duracion(
                funcion["duracion_minutos"]
            )
        except (TypeError, ValueError) as error:
            raise ValueError(
                "La duración de una película existente no es válida."
            ) from error

        if duracion_existente <= 0:
            raise ValueError(
                "La duración de una película existente debe ser positiva."
            )

        fin_existente = inicio_existente + timedelta(
            minutes=duracion_existente
        )

        if inicio_nueva < fin_existente and fin_nueva > inicio_existente:
            return True

    return False


def crear_funcion_servicio(cursor, data):
    id_pelicula = data["id_pelicula"]
    id_sala = data["id_sala"]
    fecha_hora_inicio = data["fecha_hora_inicio"]
    precio_base = data["precio_base"]

    pelicula = obtener_pelicula_por_id(cursor, id_pelicula)
    duracion = validar_duracion_pelicula(pelicula)

    if not obtener_sala_por_id(cursor, id_sala):
        raise ValueError("La sala especificada no existe.")

    if verificar_solapamiento_servicio(
        cursor, id_sala, fecha_hora_inicio, duracion
    ):
        raise ValueError(
            "La sala ya se encuentra ocupada en ese rango horario por otra función."
        )

    return crear_funcion(
        cursor, id_pelicula, id_sala, fecha_hora_inicio, precio_base
    )


def modificar_funcion_servicio(cursor, id_funcion, data):
    id_pelicula = data["id_pelicula"]
    id_sala = data["id_sala"]
    fecha_hora_inicio = data["fecha_hora_inicio"]
    precio_base = data["precio_base"]

    funcion_actual = obtener_funcion_por_id(cursor, id_funcion)

    if not funcion_actual:
        raise LookupError("No existe una función con ese ID.")

    pelicula = obtener_pelicula_por_id(cursor, id_pelicula)

    if not pelicula:
        raise ValueError("No existe la película indicada.")

    if not obtener_sala_por_id(cursor, id_sala):
        raise ValueError("No existe la sala indicada.")

    entradas_vendidas = contar_entradas_por_funcion(cursor, id_funcion)

    horario_actual = funcion_actual["fecha_hora_inicio"]
    horario_nuevo = datetime.fromisoformat(
        str(fecha_hora_inicio).replace(" ", "T")
    )

    if entradas_vendidas > 0:
        if (
            id_pelicula != funcion_actual["id_pelicula"]
            or id_sala != funcion_actual["id_sala"]
            or horario_nuevo != horario_actual
        ):
            raise ValueError(
                "No se puede modificar la película, la sala ni el horario "
                "porque ya existen entradas vendidas para esta función."
            )

    duracion = validar_duracion_pelicula(pelicula)

    if verificar_solapamiento_servicio(
        cursor,
        id_sala,
        horario_nuevo,
        duracion,
        id_funcion_excluir=id_funcion,
    ):
        raise ValueError(
            "La sala ya se encuentra ocupada en ese rango horario por otra función."
        )

    return modificar_funcion(
        cursor,
        id_funcion,
        id_pelicula,
        id_sala,
        horario_nuevo,
        precio_base,
    )
