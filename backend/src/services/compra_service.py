import uuid
from decimal import Decimal

from backend.src.constants import (
    ESTADO_COMPRA_CONFIRMADA,
    ESTADO_COMPRA_EXPIRADA,
    ESTADO_COMPRA_PENDIENTE,
)

from backend.src.validators.inicio_funcion_validator import validar_inicio_funcion

from backend.src.repositories.reservas_repositories import limpiar_reservas_expiradas

from backend.src.repositories.compra_repository import (
    obtener_funcion,
    obtener_hora_actual,
    obtener_inicio_funciones_compra,
    obtener_usuario,
    obtener_butacas_de_funcion,
    obtener_butacas_ocupadas,
    crear_compra,
    crear_entrada,
    obtener_entradas_por_compra,
    obtener_compra_para_confirmar,
    actualizar_estado_compra,
    liberar_entradas_compra,
    actualizar_qr_entrada,
)

from backend.src.services.comprobante_service import obtener_comprobante
from backend.src.services.correo_service import enviar_mail_compra


def crear_error(codigo, mensaje):
    return [{
        'code': codigo,
        'message': mensaje,
        'level': 'error'
    }]


def realizar_compra(cursor, id_usuario, id_funcion, ids_butacas):

    usuario = obtener_usuario(cursor, id_usuario)

    if usuario is None:
        return None, crear_error(
            'USUARIO_NO_EXISTE',
            'El usuario no existe.'
        )

    funcion = obtener_funcion(cursor, id_funcion)

    if funcion is None:
        return None, crear_error(
            'FUNCION_NO_EXISTE',
            'La función no existe.'
        )

    try:
        validar_inicio_funcion(
            funcion["fecha_hora_inicio"],
            obtener_hora_actual(cursor)
        )
    except ValueError as error:
        return None, crear_error(
            'FUNCION_NO_DISPONIBLE',
            str(error)
        )

    if not ids_butacas:
        return None, crear_error(
            'BUTACAS_REQUERIDAS',
            'Debe seleccionar al menos una butaca.'
        )

    if len(ids_butacas) != len(set(ids_butacas)):
        return None, crear_error(
            'BUTACAS_REPETIDAS',
            'No se pueden seleccionar butacas repetidas.'
        )

    butacas_disponibles = obtener_butacas_de_funcion(
        cursor,
        id_funcion
    )

    ids_validos = {
        butaca["id_butaca"]
        for butaca in butacas_disponibles
    }

    for id_butaca in ids_butacas:
        if id_butaca not in ids_validos:
            return None, crear_error(
                'BUTACA_INVALIDA',
                'Una o más butacas no pertenecen a esta función.'
            )

    limpiar_reservas_expiradas(cursor, id_funcion)

    butacas_ocupadas = obtener_butacas_ocupadas(
        cursor,
        id_funcion
    )

    ids_ocupados = {
        butaca["id_butaca"]
        for butaca in butacas_ocupadas
    }

    for id_butaca in ids_butacas:
        if id_butaca in ids_ocupados:
            return None, crear_error(
                'BUTACA_NO_DISPONIBLE',
                'Una o más butacas ya no están disponibles.'
            )

    precio = Decimal(str(funcion["precio_base"]))
    total = precio * len(ids_butacas)

    id_compra = crear_compra(
        cursor,
        id_usuario,
        total,
        ESTADO_COMPRA_CONFIRMADA
    )

    entradas = []

    for id_butaca in ids_butacas:
        qr_token = str(uuid.uuid4())

        id_entrada = crear_entrada(
            cursor,
            id_compra,
            id_funcion,
            id_butaca,
            qr_token
        )

        entradas.append({
            "id_entrada": id_entrada,
            "id_butaca": id_butaca,
            "qr_token": qr_token
        })

    resultado = {
        "id_compra": id_compra,
        "total": str(total),
        "estado": ESTADO_COMPRA_CONFIRMADA,
        "entradas": entradas
    }

    return resultado, None


def confirmar_compra(cursor, id_usuario, id_compra):

    compra = obtener_compra_para_confirmar(cursor, id_compra)

    if compra is None:
        return None, crear_error(
            'COMPRA_NO_EXISTE',
            'La compra no existe.'
        )

    if compra["id_usuario"] != id_usuario:
        return None, crear_error(
            'COMPRA_NO_AUTORIZADA',
            'La compra no pertenece al usuario.'
        )

    if compra["estado"] != ESTADO_COMPRA_PENDIENTE:
        return None, crear_error(
            'COMPRA_NO_PENDIENTE',
            'La compra no se encuentra pendiente.'
        )

    if not compra["vigente"]:

        filas_actualizadas = actualizar_estado_compra(
            cursor,
            id_compra,
            ESTADO_COMPRA_EXPIRADA,
            ESTADO_COMPRA_PENDIENTE
        )

        if filas_actualizadas != 1:
            return None, crear_error(
                'ERROR_ACTUALIZAR_RESERVA',
                'No se pudo actualizar el estado de la reserva.'
            )

        liberar_entradas_compra(cursor, id_compra)

        return {"reserva_vencida": True}, None

    entradas = obtener_entradas_por_compra(
        cursor,
        id_compra,
        solo_activas=True
    )

    if not entradas:
        return None, crear_error(
            'ENTRADAS_NO_ENCONTRADAS',
            'La compra no tiene entradas activas.'
        )

    primer_inicio = obtener_inicio_funciones_compra(
        cursor,
        id_compra
    )

    try:
        validar_inicio_funcion(
            primer_inicio,
            obtener_hora_actual(cursor)
        )
    except ValueError as error:
        return None, crear_error(
            'FUNCION_NO_DISPONIBLE',
            str(error)
        )

    filas_actualizadas = actualizar_estado_compra(
        cursor,
        id_compra,
        ESTADO_COMPRA_CONFIRMADA,
        ESTADO_COMPRA_PENDIENTE
    )

    if filas_actualizadas != 1:
        return None, crear_error(
            'ERROR_CONFIRMAR_COMPRA',
            'No se pudo confirmar la compra.'
        )

    entradas_confirmadas = []

    for entrada in entradas:
        qr_token = str(uuid.uuid4())

        actualizar_qr_entrada(
            cursor,
            entrada["id_entrada"],
            qr_token
        )

        entradas_confirmadas.append({
            "id_entrada": entrada["id_entrada"],
            "id_butaca": entrada["id_butaca"],
            "qr_token": qr_token
        })

    resultado = {
        "id_compra": id_compra,
        "total": str(compra["total"]),
        "estado": ESTADO_COMPRA_CONFIRMADA,
        "entradas": entradas_confirmadas
    }

    return resultado, None


def enviar_comprobante_compra(id_compra, id_usuario, entradas):

    try:
        comprobante = obtener_comprobante(id_compra, id_usuario)

        if comprobante is None:
            return {
                "correo_enviado": False,
                "mensaje_correo": "No se pudo obtener el comprobante."
            }

        enviar_mail_compra(comprobante, entradas)

        return {
            "correo_enviado": True,
            "mensaje_correo": "El comprobante se envió correctamente."
        }

    except Exception as error:
        print(f"Error al enviar el comprobante: {error}")

        return {
            "correo_enviado": False,
            "mensaje_correo": "La compra se realizó, pero no se pudo enviar el correo."
        }