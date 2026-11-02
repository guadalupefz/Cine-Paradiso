
import uuid
from decimal import Decimal

from backend.db.db import get_connection
from backend.src.repositories.compra_repository import (
    obtener_funcion,
    obtener_usuario,
    obtener_butacas_de_funcion,
    obtener_butacas_ocupadas,
    crear_compra,
    crear_entrada
)

from backend.src.services.comprobante_service import obtener_comprobante
from backend.src.services.correo_service import enviar_mail_compra


def realizar_compra(id_usuario, id_funcion, ids_butacas):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        usuario = obtener_usuario(cursor, id_usuario)

        if usuario is None:
            raise ValueError("El usuario no existe.")
        funcion = obtener_funcion(cursor, id_funcion)

        if funcion is None:
            raise ValueError("La función no existe.")

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
            "aprobada"
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
            "estado": "aprobada",
            "entradas": entradas
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

    try:
        comprobante = obtener_comprobante(id_compra, id_usuario)

        enviar_mail_compra(comprobante, entradas)

    except Exception as error:
        print(f"no se pudo enviar el correo: {error}")

    return resultado