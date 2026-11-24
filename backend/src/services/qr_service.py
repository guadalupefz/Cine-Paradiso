from datetime import datetime, timedelta
from io import BytesIO

import qrcode

from backend.src.constants import ESTADO_COMPRA_CONFIRMADA
from backend.src.repositories.qr_repository import (
    validar_entrada,
    marcar_entrada_usada,
    obtener_entrada_para_qr,
)


def entrada_utilizada(entrada):
    return entrada["fecha_hora_validacion"] is not None


def compra_confirmada(entrada):
    return entrada["estado_compra"].lower() == ESTADO_COMPRA_CONFIRMADA


def funcion_correcta(entrada, id_funcion_a_validar):
    return entrada["id_funcion"] == id_funcion_a_validar


def horario_correcto(entrada):
    inicio = entrada["fecha_hora_inicio"]
    ahora = datetime.now()
    desde = inicio - timedelta(minutes=30)
    hasta = inicio + timedelta(minutes=30)
    return desde <= ahora <= hasta


def generar_qr(qr_token):
    return qrcode.make(qr_token)


def validar_qr_service(cursor, qr_token, id_funcion):
    entrada = validar_entrada(cursor, qr_token)

    if entrada is None:
        return None, {
            "error": "QR_NO_ENCONTRADO",
            "mensaje": "No existe una entrada con ese QR."
        }

    if entrada_utilizada(entrada):
        return None, {
            "error": "QR_YA_UTILIZADO",
            "mensaje": "Esta entrada ya se usó."
        }

    if not compra_confirmada(entrada):
        return None, {
            "error": "COMPRA_NO_CONFIRMADA",
            "mensaje": "La compra no está confirmada."
        }

    if not funcion_correcta(entrada, id_funcion):
        return None, {
            "error": "FUNCION_INCORRECTA",
            "mensaje": "La entrada no corresponde a esta función."
        }

    if not horario_correcto(entrada):
        return None, {
            "error": "HORARIO_INCORRECTO",
            "mensaje": "La entrada está fuera del horario permitido."
        }

    filas_actualizadas = marcar_entrada_usada(
        cursor, entrada["id_entrada"]
    )

    if filas_actualizadas != 1:
        return None, {
            "error": "QR_NO_ACTUALIZADO",
            "mensaje": "No se pudo realizar el ingreso."
        }

    return {
        "valida": True,
        "mensaje": "Entrada validada correctamente.",
        "id_entrada": entrada["id_entrada"]
    }, None


def obtener_qr_imagen_service(cursor, id_entrada, id_usuario):
    entrada = obtener_entrada_para_qr(cursor, id_entrada, id_usuario)

    if entrada is None:
        return None, {
            "error": "ENTRADA_NO_ENCONTRADA",
            "mensaje": "No se encontró la entrada."
        }

    imagen = generar_qr(entrada["qr_token"])
    archivo = BytesIO()
    imagen.save(archivo, format="PNG")
    archivo.seek(0)

    return archivo, None
