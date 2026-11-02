from datetime import datetime, timedelta
from decimal import Decimal
import mysql.connector

from src.db import get_connection
from src.repositories.reservas_repositories import (
    obtener_butacas_ocupadas_con_bloqueo,
    limpiar_reservas_expiradas,
    obtener_precio_base_funcion,
    crear_compra_pendiente,
    crear_entradas_reserva
)

TIEMPO_EXPIRACION_MINUTOS = 15

def crear_reserva(id_usuario: int, id_funcion: int, lista_id_butacas: list):
    conn = None
    try:
        conn = get_connection()
        conn.start_transaction()

        with conn.cursor(dictionary=True) as cursor:
            # Verificar existencia de la función y obtener precio base
            precio_base = obtener_precio_base_funcion(cursor, id_funcion)
            if precio_base is None:
                conn.rollback()
                return None, {
                    "error": "FUNCION_NO_ENCONTRADA",
                    "mensaje": "La función especificada no existe.",
                    "status_code": 404
                }
            
            # Limpiar automáticamente reservas caducadas previas (>15 min)
            limpiar_reservas_expiradas(cursor, id_funcion, lista_id_butacas)

            # Bloqueo pesimista (FOR UPDATE) y detección de conflictos
            ocupadas = obtener_butacas_ocupadas_con_bloqueo(cursor, id_funcion, lista_id_butacas)
            if ocupadas:
                conn.rollback()
                return None, {
                    "error": "BUTACAS_OCUPADAS",
                    "mensaje": "Una o más butacas seleccionadas ya están reservadas o vendidas.",
                    "butacas_conflictivas": ocupadas,
                    "status_code": 409
                }
            
            # Cálculo automático del importe total en el Backend
            total_calculado = Decimal(str(precio_base)) * len(lista_id_butacas)

            # Insertar encabezado en 'compra' (estado 'pendiente')
            id_compra = crear_compra_pendiente(cursor, id_usuario, total_calculado)

            # Crear los registros correspondientes en 'entrada'
            crear_entradas_reserva(cursor, id_compra, id_funcion, lista_id_butacas)
            
            # Confirmación atómica de la transacción
            conn.commit()
            fecha_vencimiento = datetime.now() + timedelta(minutes=TIEMPO_EXPIRACION_MINUTOS)
            reserva = {
                "id_compra": id_compra,
                "id_usuario": id_usuario,
                "id_funcion": id_funcion,
                "butacas": lista_id_butacas,
                "total": float(total_calculado),
                "estado": "pendiente",
                "fecha_hora_vencimiento": fecha_vencimiento.strftime("%Y-%m-%d %H:%M:%S")
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