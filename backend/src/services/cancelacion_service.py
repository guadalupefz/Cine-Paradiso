from backend.src.constants import (
    ESTADO_COMPRA_CANCELADA,
    ESTADO_COMPRA_CONFIRMADA,
)
from backend.src.repositories import compra_repository as repo


ESTADOS_CANCELABLES = (
    ESTADO_COMPRA_CONFIRMADA,
    "aprobada",
)


def cancelar_compra(cursor, id_usuario, id_compra):
    compra = repo.obtener_compra_para_cancelar(
        cursor, id_compra, id_usuario
    )

    if compra is None:
        return None, "COMPRA_NO_ENCONTRADA"

    if compra["estado"] not in ESTADOS_CANCELABLES:
        return None, "ESTADO_NO_CANCELABLE"

    entradas = repo.obtener_entradas_para_cancelar(
        cursor, id_compra
    )

    if not entradas:
        return None, "COMPRA_SIN_ENTRADAS"

    entradas_utilizadas = any(
        entrada["fecha_hora_validacion"] is not None
        for entrada in entradas
    )

    if entradas_utilizadas:
        return None, "ENTRADAS_UTILIZADAS"

    fuera_de_plazo = any(
        entrada["fuera_de_plazo"]
        for entrada in entradas
    )

    if fuera_de_plazo:
        return None, "FUERA_DE_PLAZO"

    repo.actualizar_estado_compra(
        cursor,
        id_compra,
        ESTADO_COMPRA_CANCELADA,
        compra["estado"]
    )

    repo.liberar_entradas_compra(cursor, id_compra)

    return {
        "id_compra": id_compra,
        "estado": ESTADO_COMPRA_CANCELADA,
        "mensaje": "Compra cancelada correctamente"
    }, None
