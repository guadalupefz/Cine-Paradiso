from datetime import datetime, timedelta

import qrcode

def entrada_utilizada(entrada):

    if entrada["fecha_hora_validacion"] is not None:

        return True

    return False


def compra_confirmada(entrada):
    if entrada["estado_compra"].lower() in ("confirmada", "aprobada"):
        return True

    return False


def funcion_correcta(entrada, id_funcion_a_validar):
    if entrada["id_funcion"] == id_funcion_a_validar:
        return True

    return False

#tomamos que se puede entrar desde 3o minutos antes hasta 30 minutos despues
def horario_correcto(entrada):
    inicio = entrada["fecha_hora_inicio"]
    ahora = datetime.now()

    desde = inicio - timedelta(minutes=30)
    hasta = inicio + timedelta(minutes=30)

    if desde <= ahora and ahora <= hasta:
        return True

    return False


def generar_qr(qr_token):
    return qrcode.make(qr_token)