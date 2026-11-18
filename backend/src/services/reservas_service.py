from datetime import timedelta
from decimal import Decimal

from backend.src.constants import (
    ESTADO_COMPRA_CANCELADA,
    ESTADO_COMPRA_EXPIRADA,
    ESTADO_COMPRA_PENDIENTE,
    ESTADO_COMPRA_RECHAZADA,
    RESERVA_DURACION_MINUTOS,
)
from backend.src.repositories.compra_repository import (
    obtener_butacas_de_funcion,
    obtener_funcion,
    obtener_hora_actual,
)
from backend.src.repositories.reservas_repositories import (
    actualizar_estado_compra,
    actualizar_total_compra,
    agregar_servicio_a_compra,
    crear_compra_pendiente,
    crear_entradas_reserva,
    eliminar_entradas_reserva,
    eliminar_servicios_reserva,
    limpiar_reservas_expiradas,
    liberar_entradas_reserva,
    obtener_butacas_ocupadas_con_bloqueo,
    obtener_butacas_ocupadas_para_edicion,
    obtener_compra_reserva_para_actualizar,
    obtener_funcion_de_reserva,
    reserva_vencida,
)
from backend.src.repositories.servicios_repository import obtener_servicio
from backend.src.validators.inicio_funcion_validator import validar_inicio_funcion


def _error(error, mensaje, status_code):
    return {
        "error": error,
        "mensaje": mensaje,
        "status_code": status_code,
    }


def _expirar_reserva(cursor, id_compra):
    actualizar_estado_compra(cursor, id_compra, ESTADO_COMPRA_EXPIRADA)
    liberar_entradas_reserva(cursor, id_compra)
    return _error("RESERVA_EXPIRADA", "La reserva ya venció.", 409)


def crear_reserva(
    cursor,
    id_usuario: int,
    id_funcion: int,
    lista_id_butacas: list,
    servicios: list | None = None,
):
    if servicios is None:
        servicios = []

    funcion = obtener_funcion(cursor, id_funcion)
    if funcion is None:
        return None, _error(
            "FUNCION_NO_ENCONTRADA",
            "La función especificada no existe.",
            404,
        )

    try:
        validar_inicio_funcion(
            funcion["fecha_hora_inicio"], obtener_hora_actual(cursor)
        )
    except ValueError as error:
        return None, _error("FUNCION_INICIADA", str(error), 400)

    precio_base = funcion["precio_base"]

    # Locking the function serializes reservations even before an entry exists.
    butacas_sala = obtener_butacas_de_funcion(cursor, id_funcion)
    ids_validos = {butaca["id_butaca"] for butaca in butacas_sala}
    if any(id_butaca not in ids_validos for id_butaca in lista_id_butacas):
        return None, _error(
            "BUTACAS_INVALIDAS",
            "Una o más butacas no pertenecen a la sala de esta función.",
            400,
        )

    limpiar_reservas_expiradas(cursor, id_funcion)
    ocupadas = obtener_butacas_ocupadas_con_bloqueo(
        cursor, id_funcion, lista_id_butacas
    )
    if ocupadas:
        error = _error(
            "BUTACAS_OCUPADAS",
            "Una o más butacas seleccionadas ya están reservadas o vendidas.",
            409,
        )
        error["butacas_conflictivas"] = ocupadas
        return None, error

    total_entradas = Decimal(str(precio_base)) * len(lista_id_butacas)
    total_servicios = Decimal("0.00")
    servicios_a_guardar = []

    for servicio in servicios:
        id_servicio = servicio["id_servicio"]
        cantidad = servicio["cantidad"]
        servicio_db = obtener_servicio(cursor, id_servicio)

        if servicio_db is None:
            return None, _error(
                "SERVICIO_NO_ENCONTRADO",
                f"El servicio {id_servicio} no existe.",
                404,
            )

        precio_unitario = Decimal(str(servicio_db["precio"]))
        total_servicios += precio_unitario * cantidad
        servicios_a_guardar.append({
            "id_servicio": id_servicio,
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
        })

    total_calculado = total_entradas + total_servicios
    fecha_hora_creacion = obtener_hora_actual(cursor)
    id_compra = crear_compra_pendiente(
        cursor, id_usuario, total_calculado, fecha_hora_creacion
    )
    crear_entradas_reserva(cursor, id_compra, id_funcion, lista_id_butacas)

    for servicio in servicios_a_guardar:
        agregar_servicio_a_compra(
            cursor,
            id_compra,
            servicio["id_servicio"],
            servicio["cantidad"],
            servicio["precio_unitario"],
        )

    fecha_vencimiento = fecha_hora_creacion + timedelta(
        minutes=RESERVA_DURACION_MINUTOS
    )
    return {
        "id_compra": id_compra,
        "id_usuario": id_usuario,
        "id_funcion": id_funcion,
        "butacas": lista_id_butacas,
        "servicios": servicios_a_guardar,
        "total": float(total_calculado),
        "estado": ESTADO_COMPRA_PENDIENTE,
        "fecha_hora_vencimiento": fecha_vencimiento.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }, None


def _obtener_reserva_pendiente(cursor, id_compra, id_usuario, mensaje_estado):
    compra = obtener_compra_reserva_para_actualizar(
        cursor, id_compra, id_usuario
    )
    if compra is None:
        return None, _error(
            "RESERVA_NO_ENCONTRADA", "No se encontró la reserva.", 404
        )

    if compra["estado"] != ESTADO_COMPRA_PENDIENTE:
        return None, _error("RESERVA_NO_PENDIENTE", mensaje_estado, 409)

    if reserva_vencida(cursor, id_compra):
        return None, _expirar_reserva(cursor, id_compra)

    return compra, None


def rechazar_reserva_pendiente(cursor, id_compra: int, id_usuario: int):
    _, error = _obtener_reserva_pendiente(
        cursor,
        id_compra,
        id_usuario,
        "La reserva no se encuentra pendiente.",
    )
    if error:
        return None, error

    actualizar_estado_compra(cursor, id_compra, ESTADO_COMPRA_RECHAZADA)
    liberar_entradas_reserva(cursor, id_compra)
    return {"id_compra": id_compra, "estado": ESTADO_COMPRA_RECHAZADA}, None


def abandonar_reserva_pendiente(cursor, id_compra: int, id_usuario: int):
    _, error = _obtener_reserva_pendiente(
        cursor,
        id_compra,
        id_usuario,
        "La reserva no se encuentra pendiente.",
    )
    if error:
        return None, error

    actualizar_estado_compra(cursor, id_compra, ESTADO_COMPRA_CANCELADA)
    liberar_entradas_reserva(cursor, id_compra)
    return {"id_compra": id_compra, "estado": ESTADO_COMPRA_CANCELADA}, None


def editar_reserva_pendiente(
    cursor,
    id_compra: int,
    id_usuario: int,
    lista_id_butacas: list,
    servicios: list | None = None,
):
    if servicios is None:
        servicios = []

    _, error = _obtener_reserva_pendiente(
        cursor,
        id_compra,
        id_usuario,
        "Solo se pueden editar reservas pendientes.",
    )
    if error:
        return None, error

    entrada_actual = obtener_funcion_de_reserva(cursor, id_compra)
    if entrada_actual is None:
        return None, _error(
            "RESERVA_SIN_ENTRADAS",
            "No se encontraron entradas asociadas a la reserva.",
            409,
        )

    id_funcion = entrada_actual["id_funcion"]
    funcion = obtener_funcion(cursor, id_funcion)
    if funcion is None:
        return None, _error(
            "FUNCION_NO_ENCONTRADA",
            "La función asociada a la reserva no existe.",
            404,
        )

    try:
        validar_inicio_funcion(
            funcion["fecha_hora_inicio"], obtener_hora_actual(cursor)
        )
    except ValueError as error:
        return None, _error("FUNCION_INICIADA", str(error), 400)

    butacas_sala = obtener_butacas_de_funcion(cursor, id_funcion)
    ids_validos = {butaca["id_butaca"] for butaca in butacas_sala}
    if any(id_butaca not in ids_validos for id_butaca in lista_id_butacas):
        return None, _error(
            "BUTACAS_INVALIDAS",
            "Una o más butacas no pertenecen a la sala de esta función.",
            400,
        )

    ocupadas = obtener_butacas_ocupadas_para_edicion(
        cursor, id_funcion, lista_id_butacas, id_compra
    )
    if ocupadas:
        error = _error(
            "BUTACAS_OCUPADAS",
            "Una o más butacas seleccionadas ya están reservadas o vendidas.",
            409,
        )
        error["butacas_conflictivas"] = ocupadas
        return None, error

    total_entradas = Decimal(str(funcion["precio_base"])) * len(lista_id_butacas)
    total_servicios = Decimal("0.00")
    servicios_a_guardar = []
    for servicio in servicios:
        servicio_db = obtener_servicio(cursor, servicio["id_servicio"])
        if servicio_db is None:
            return None, _error(
                "SERVICIO_NO_ENCONTRADO",
                f"El servicio {servicio['id_servicio']} no existe.",
                404,
            )

        precio_unitario = Decimal(str(servicio_db["precio"]))
        cantidad = servicio["cantidad"]
        total_servicios += precio_unitario * cantidad
        servicios_a_guardar.append({
            "id_servicio": servicio["id_servicio"],
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
        })

    eliminar_entradas_reserva(cursor, id_compra)
    crear_entradas_reserva(cursor, id_compra, id_funcion, lista_id_butacas)
    eliminar_servicios_reserva(cursor, id_compra)
    for servicio in servicios_a_guardar:
        agregar_servicio_a_compra(
            cursor,
            id_compra,
            servicio["id_servicio"],
            servicio["cantidad"],
            servicio["precio_unitario"],
        )

    total = total_entradas + total_servicios
    actualizar_total_compra(cursor, id_compra, total)
    return {
        "id_compra": id_compra,
        "id_funcion": id_funcion,
        "butacas": lista_id_butacas,
        "servicios": servicios_a_guardar,
        "total": float(total),
        "estado": ESTADO_COMPRA_PENDIENTE,
    }, None
