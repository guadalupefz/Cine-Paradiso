
import uuid
from decimal import Decimal
from datetime import datetime, timedelta

from backend.db.db import get_connection
from backend.src.constants import (
    ESTADO_COMPRA_CONFIRMADA,
    ESTADO_COMPRA_EXPIRADA,
    ESTADO_COMPRA_PENDIENTE,
    RESERVA_DURACION_MINUTOS,
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
    obtener_compra_por_id,
    obtener_entradas_por_compra
)

from backend.src.services.comprobante_service import obtener_comprobante
from backend.src.services.correo_service import enviar_mail_compra


def realizar_compra(id_usuario, id_funcion, ids_butacas):
    conn = get_connection()
    cursor = None

    try:
        cursor = conn.cursor(dictionary=True)
        usuario = obtener_usuario(cursor, id_usuario)

        if usuario is None:
            raise ValueError("El usuario no existe.")

        funcion = obtener_funcion(cursor, id_funcion)

        if funcion is None:
            raise ValueError("La función no existe.")

        validar_inicio_funcion(funcion["fecha_hora_inicio"], obtener_hora_actual(cursor))

        if not ids_butacas:
            raise ValueError("Debe seleccionar al menos una butaca.")

        if len(ids_butacas) != len(set(ids_butacas)):
            raise ValueError("No se pueden seleccionar butacas repetidas.")

        butacas_disponibles = obtener_butacas_de_funcion(cursor, id_funcion)
        ids_validos = {b["id_butaca"] for b in butacas_disponibles}

        for id_butaca in ids_butacas:
            if id_butaca not in ids_validos:
                raise ValueError(
                    f"La butaca {id_butaca} no pertenece a la sala de esta función."
                )

        limpiar_reservas_expiradas(cursor, id_funcion)
        butacas_ocupadas = obtener_butacas_ocupadas(cursor, id_funcion)
        ids_ocupados = {b["id_butaca"] for b in butacas_ocupadas}

        for id_butaca in ids_butacas:
            if id_butaca in ids_ocupados:
                raise ValueError(f"La butaca {id_butaca} ya está ocupada.")

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

        conn.commit()

        resultado = {
            "id_compra": id_compra,
            "total": str(total),
            "estado": ESTADO_COMPRA_CONFIRMADA,
            "entradas": entradas
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        conn.close()

    try:
        comprobante = obtener_comprobante(id_compra, id_usuario)

        if comprobante is None:
            raise ValueError("No se pudo obtener el comprobante.")

        enviar_mail_compra(comprobante, entradas)

        resultado["correo_enviado"] = True
        resultado["mensaje_correo"] = "El comprobante fue enviado por correo."

    except Exception as error:
        print(f"No se pudo enviar el correo: {error}")

        resultado["correo_enviado"] = False
        resultado["mensaje_correo"] = (
            "La compra fue confirmada, pero no se pudo enviar el correo. "
            "Podés consultar tus entradas desde tu cuenta."
        )

    return resultado


def confirmar_compra(id_usuario, id_compra):
    conn = get_connection()
    cursor = None

    try:
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()

        cursor.execute(
            """
            SELECT id_compra, id_usuario, fecha_hora, total, estado,
                   (TIMESTAMPADD(MINUTE, %s, fecha_hora) > NOW()) AS vigente
            FROM compra
            WHERE id_compra = %s
            FOR UPDATE
            """,
            (RESERVA_DURACION_MINUTOS, id_compra)
        )

        compra = cursor.fetchone()

        if compra is None:
            raise ValueError("La compra no existe.")

        if compra["id_usuario"] != id_usuario:
            raise ValueError("La compra no pertenece a este usuario.")

        if compra["estado"] != ESTADO_COMPRA_PENDIENTE:
            raise ValueError("La compra no está pendiente de confirmación.")

        if not compra["vigente"]:
            cursor.execute(
                """
                UPDATE compra
                SET estado = %s
                WHERE id_compra = %s
                """,
                (ESTADO_COMPRA_EXPIRADA, id_compra)
            )

            cursor.execute(
                """
                UPDATE entrada
                SET ocupacion_activa = NULL
                WHERE id_compra = %s
                """,
                (id_compra,)
            )

            conn.commit()
            raise ValueError(
            "La reserva venció. Debe realizar una nueva reserva"
            )

        entradas = obtener_entradas_por_compra(cursor,id_compra,solo_activas=True)

        if not entradas:
            raise ValueError("La compra no tiene entradas asociadas.")

        primer_inicio = obtener_inicio_funciones_compra(cursor, id_compra)
        validar_inicio_funcion(primer_inicio, obtener_hora_actual(cursor))

        cursor.execute(
            """
            UPDATE compra
            SET estado = %s
            WHERE id_compra = %s AND estado = %s
            """,
            (ESTADO_COMPRA_CONFIRMADA, id_compra, ESTADO_COMPRA_PENDIENTE)
        )

        if cursor.rowcount != 1:
            raise ValueError("No se pudo confirmar la compra.")

        entradas_confirmadas = []

        for entrada in entradas:
            qr_token = str(uuid.uuid4())

            cursor.execute(
                """
                UPDATE entrada
                SET qr_token = %s
                WHERE id_entrada = %s
                """,
                (qr_token, entrada["id_entrada"])
            )

            entradas_confirmadas.append({
                "id_entrada": entrada["id_entrada"],
                "id_butaca": entrada["id_butaca"],
                "qr_token": qr_token
            })

        conn.commit()

        resultado = {
            "id_compra": id_compra,
            "total": str(compra["total"]),
            "estado": ESTADO_COMPRA_CONFIRMADA,
            "entradas": entradas_confirmadas
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        conn.close()

    try:
        comprobante = obtener_comprobante(id_compra, id_usuario)

        if comprobante is None:
            raise ValueError("No se pudo obtener el comprobante.")

        enviar_mail_compra(comprobante, entradas_confirmadas)

        resultado["correo_enviado"] = True
        resultado["mensaje_correo"] = "El comprobante fue enviado por correo."

    except Exception as error:
        print(f"No se pudo enviar el correo: {error}")

        resultado["correo_enviado"] = False
        resultado["mensaje_correo"] = (
            "La reserva fue confirmada, pero no se pudo enviar el correo. "
            "Podés consultar tus entradas desde tu cuenta."
        )

    return resultado