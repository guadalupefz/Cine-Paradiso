from datetime import datetime, timedelta
from decimal import Decimal
import mysql.connector

from backend.db.db import get_connection

from backend.src.repositories.servicios_repository import obtener_servicio

from backend.src.repositories.reservas_repositories import (obtener_butacas_ocupadas_con_bloqueo,
    limpiar_reservas_expiradas, obtener_precio_base_funcion, crear_compra_pendiente,
    crear_entradas_reserva, agregar_servicio_a_compra
)

TIEMPO_EXPIRACION_MINUTOS = 15

def crear_reserva(id_usuario: int, id_funcion: int,
    lista_id_butacas: list, servicios: list = None
):
    if servicios is None:
        servicios = []

    conn = None

    try:
        conn = get_connection()
        conn.start_transaction()

        with conn.cursor(dictionary=True) as cursor:

            # Consultar precio de la función
            precio_base = obtener_precio_base_funcion(cursor, id_funcion)

            if precio_base is None:
                conn.rollback()
                return None, {
                    "error": "FUNCION_NO_ENCONTRADA",
                    "mensaje": "La función especificada no existe.",
                    "status_code": 404
                }

            # Limpiar reservas vencidas
            limpiar_reservas_expiradas(
                cursor, id_funcion, lista_id_butacas
            )

            # Comprobar disponibilidad de butacas
            ocupadas = obtener_butacas_ocupadas_con_bloqueo(
                cursor, id_funcion, lista_id_butacas
            )

            if ocupadas:
                conn.rollback()
                return None, {
                    "error": "BUTACAS_OCUPADAS",
                    "mensaje": "Una o más butacas seleccionadas ya están reservadas o vendidas.",
                    "butacas_conflictivas": ocupadas,
                    "status_code": 409
                }

            # Calcular precio de las entradas
            total_entradas = (
                Decimal(str(precio_base)) * len(lista_id_butacas)
            )

            total_servicios = Decimal("0.00")
            servicios_a_guardar = []

            # Consultar y calcular los servicios seleccionados
            for servicio in servicios:

                id_servicio = servicio["id_servicio"]
                cantidad = servicio["cantidad"]

                servicio_db = obtener_servicio(cursor, id_servicio)

                if servicio_db is None:
                    conn.rollback()
                    return None, {
                        "error": "SERVICIO_NO_ENCONTRADO",
                        "mensaje": f"El servicio {id_servicio} no existe.",
                        "status_code": 404
                    }

                precio_unitario = Decimal(str(servicio_db["precio"]))
                subtotal = precio_unitario * cantidad

                total_servicios += subtotal

                servicios_a_guardar.append({
                    "id_servicio": id_servicio,
                    "cantidad": cantidad,
                    "precio_unitario": precio_unitario
                })

            # Calcular total general
            total_calculado = total_entradas + total_servicios

            # Crear una única compra pendiente
            id_compra = crear_compra_pendiente(
                cursor, id_usuario, total_calculado
            )

            # Crear las entradas de la reserva
            crear_entradas_reserva(
                cursor, id_compra, id_funcion, lista_id_butacas
            )

            # Guardar los servicios asociados a esa misma compra
            for servicio in servicios_a_guardar:
                agregar_servicio_a_compra(
                    cursor,
                    id_compra,
                    servicio["id_servicio"],
                    servicio["cantidad"],
                    servicio["precio_unitario"]
                )

            conn.commit()

            fecha_vencimiento = (
                datetime.now() +
                timedelta(minutes=TIEMPO_EXPIRACION_MINUTOS)
            )

            reserva = {
                "id_compra": id_compra,
                "id_usuario": id_usuario,
                "id_funcion": id_funcion,
                "butacas": lista_id_butacas,
                "servicios": servicios_a_guardar,
                "total": float(total_calculado),
                "estado": "pendiente",
                "fecha_hora_vencimiento": fecha_vencimiento.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            }

            return reserva, None

    except mysql.connector.Error as e:
        if conn is not None:
            conn.rollback()

        return None, {
            "error": "ERROR_BASE_DATOS",
            "mensaje": "Error en la base de datos al procesar la reserva.",
            "description": str(e),
            "status_code": 500
        }

    finally:
        if conn is not None:
            conn.close()