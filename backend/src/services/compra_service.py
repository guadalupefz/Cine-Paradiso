import uuid
from decimal import Decimal
from datetime import datetime, timedelta

from backend.db.db import get_connection

from backend.src.repositories.compra_repository import (obtener_funcion,
    obtener_usuario, obtener_butacas_de_funcion, obtener_butacas_ocupadas,
    crear_compra, crear_entrada, obtener_compra_por_id,
    obtener_entradas_por_compra
)

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

def confirmar_compra(id_usuario, id_compra):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        conn.start_transaction()

        # Buscar y bloquear la compra mientras se confirma.
        cursor.execute(
            """
            SELECT id_compra, id_usuario, fecha_hora, total, estado,
                   (fecha_hora + INTERVAL 15 MINUTE > NOW()) AS vigente
            FROM compra
            WHERE id_compra = %s
            FOR UPDATE
            """,
            (id_compra,)
        )

        compra = cursor.fetchone()

        if compra is None:
            raise ValueError("La compra no existe.")

        if compra["id_usuario"] != id_usuario:
            raise ValueError("La compra no pertenece a este usuario.")

        if compra["estado"] != "pendiente":
            raise ValueError("La compra no está pendiente de confirmación.")

        
        if not compra["vigente"]:
            cursor.execute(
                """
                UPDATE compra
                SET estado = 'expirada'
                WHERE id_compra = %s
                """,
                (id_compra,)
            )
            conn.commit()
            raise ValueError("La reserva venció. Debe realizar una nueva reserva.")

        entradas = obtener_entradas_por_compra(cursor, id_compra)

        if not entradas:
            raise ValueError("La compra no tiene entradas asociadas.")

        # Confirmar la compra existente.
        cursor.execute(
            """
            UPDATE compra
            SET estado = 'aprobada'
            WHERE id_compra = %s AND estado = 'pendiente'
            """,
            (id_compra,)
        )

        if cursor.rowcount != 1:
            raise ValueError("No se pudo confirmar la compra.")

        # Reemplazar los QR temporales por QR definitivos.
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

        return {
            "id_compra": id_compra,
            "total": str(compra["total"]),
            "estado": "aprobada",
            "entradas": entradas_confirmadas
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()