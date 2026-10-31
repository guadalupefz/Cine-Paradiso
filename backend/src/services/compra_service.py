
import uuid
from decimal import Decimal

from backend.db.db import get_connection
from backend.src.repositories.compra_repository import (
    obtener_funcion,
    obtener_butacas_de_funcion,
    obtener_butacas_ocupadas,
    crear_compra,
    crear_entrada
)


def realizar_compra(id_usuario, id_funcion, ids_butacas):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Verificar que exista la función.
        funcion = obtener_funcion(cursor, id_funcion)

        if funcion is None:
            raise ValueError("La función no existe.")

        # Verificar que se hayan seleccionado butacas.
        if not ids_butacas:
            raise ValueError("Debe seleccionar al menos una butaca.")

        # Evitar que se repita una misma butaca en la solicitud.
        if len(ids_butacas) != len(set(ids_butacas)):
            raise ValueError("No se pueden seleccionar butacas repetidas.")

        # Obtener las butacas pertenecientes a la sala.
        butacas_disponibles = obtener_butacas_de_funcion(cursor, id_funcion)
        ids_validos = {b["id_butaca"] for b in butacas_disponibles}

        for id_butaca in ids_butacas:
            if id_butaca not in ids_validos:
                raise ValueError(
                    f"La butaca {id_butaca} no pertenece a la sala de esta función."
                )

        # Comprobar cuáles ya están ocupadas.
        butacas_ocupadas = obtener_butacas_ocupadas(cursor, id_funcion)
        ids_ocupados = {b["id_butaca"] for b in butacas_ocupadas}

        for id_butaca in ids_butacas:
            if id_butaca in ids_ocupados:
                raise ValueError(f"La butaca {id_butaca} ya está ocupada.")

        # Calcular el total.
        precio = Decimal(str(funcion["precio_base"]))
        total = precio * len(ids_butacas)

        # Registrar la compra.
        id_compra = crear_compra(
            cursor,
            id_usuario,
            total,
            "aprobada"
        )

        # Crear una entrada y un QR por cada butaca.
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

        return {
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
