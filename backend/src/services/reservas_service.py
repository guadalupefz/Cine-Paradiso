from datetime import timedelta
from decimal import Decimal
import mysql.connector

from backend.db.db import get_connection
from backend.src.constants import (
    ESTADO_COMPRA_CANCELADA,
    ESTADO_COMPRA_CONFIRMADA,
    ESTADO_COMPRA_EXPIRADA,
    ESTADO_COMPRA_PENDIENTE,
    ESTADO_COMPRA_RECHAZADA,
    RESERVA_DURACION_MINUTOS,
)

from backend.src.repositories.servicios_repository import obtener_servicio
from backend.src.repositories.compra_repository import obtener_butacas_de_funcion, obtener_funcion, obtener_hora_actual
from backend.src.validators.inicio_funcion_validator import validar_inicio_funcion

from backend.src.repositories.reservas_repositories import (obtener_butacas_ocupadas_con_bloqueo,
    limpiar_reservas_expiradas, crear_compra_pendiente,
    crear_entradas_reserva, agregar_servicio_a_compra
)

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

            funcion = obtener_funcion(cursor, id_funcion)

            if funcion is None:
                conn.rollback()
                return None, {
                    "error": "FUNCION_NO_ENCONTRADA",
                    "mensaje": "La función especificada no existe.",
                    "status_code": 404
                }

            try:
                validar_inicio_funcion(funcion["fecha_hora_inicio"], obtener_hora_actual(cursor))
            except ValueError as error:
                conn.rollback()
                return None, {"error": "FUNCION_INICIADA", "mensaje": str(error), "status_code": 400}
            precio_base = funcion["precio_base"]

            # La funcion ya esta bloqueada: las reservas de esta funcion se
            # resuelven en orden, incluso cuando todavia no existe una entrada.
            butacas_sala = obtener_butacas_de_funcion(cursor, id_funcion)
            ids_validos = {butaca["id_butaca"] for butaca in butacas_sala}
            if any(id_butaca not in ids_validos for id_butaca in lista_id_butacas):
                conn.rollback()
                return None, {
                    "error": "BUTACAS_INVALIDAS",
                    "mensaje": "Una o más butacas no pertenecen a la sala de esta función.",
                    "status_code": 400,
                }

            limpiar_reservas_expiradas(cursor, id_funcion)

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

            total_entradas = (
                Decimal(str(precio_base)) * len(lista_id_butacas)
            )

            total_servicios = Decimal("0.00")
            servicios_a_guardar = []

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

            total_calculado = total_entradas + total_servicios

            fecha_hora_creacion = obtener_hora_actual(cursor)
            id_compra = crear_compra_pendiente(
                cursor, id_usuario, total_calculado, fecha_hora_creacion
            )

            crear_entradas_reserva(
                cursor, id_compra, id_funcion, lista_id_butacas
            )

            for servicio in servicios_a_guardar:
                agregar_servicio_a_compra(
                    cursor,
                    id_compra,
                    servicio["id_servicio"],
                    servicio["cantidad"],
                    servicio["precio_unitario"]
                )

            conn.commit()

            fecha_vencimiento = fecha_hora_creacion + timedelta(
                minutes=RESERVA_DURACION_MINUTOS
            )

            reserva = {
                "id_compra": id_compra,
                "id_usuario": id_usuario,
                "id_funcion": id_funcion,
                "butacas": lista_id_butacas,
                "servicios": servicios_a_guardar,
                "total": float(total_calculado),
                "estado": ESTADO_COMPRA_PENDIENTE,
                "fecha_hora_vencimiento": fecha_vencimiento.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            }

            return reserva, None

    except mysql.connector.Error as e:
        if conn is not None:
            conn.rollback()

        if e.errno == 1062 and "uq_entrada_ocupacion_activa" in str(e):
            return None, {
                "error": "BUTACAS_OCUPADAS",
                "mensaje": "Una o más butacas seleccionadas ya están reservadas o vendidas.",
                "status_code": 409
            }

        if e.errno in (1205, 1213):
            return None, {
                "error": "CONFLICTO_RESERVA",
                "mensaje": "Otra operación está modificando la reserva. Volvé a intentar.",
                "status_code": 409,
            }

        return None, {
            "error": "ERROR_BASE_DATOS",
            "mensaje": "Error en la base de datos al procesar la reserva.",
            "status_code": 500
        }

    finally:
        if conn is not None:
            conn.close()


def rechazar_reserva_pendiente(id_compra: int, id_usuario: int):
    conn = None

    try:
        conn = get_connection()
        conn.start_transaction()

        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT id_compra, estado, fecha_hora
                FROM compra
                WHERE id_compra = %s AND id_usuario = %s
                FOR UPDATE
                """,
                (id_compra, id_usuario)
            )
            compra = cursor.fetchone()

            if compra is None:
                conn.rollback()
                return None, {
                    "error": "RESERVA_NO_ENCONTRADA",
                    "mensaje": "No se encontró la reserva.",
                    "status_code": 404
                }

            if compra["estado"] != ESTADO_COMPRA_PENDIENTE:
                conn.rollback()
                return None, {
                    "error": "RESERVA_NO_PENDIENTE",
                    "mensaje": "La reserva no se encuentra pendiente.",
                    "status_code": 409
                }

            cursor.execute(
                """
                SELECT TIMESTAMPADD(MINUTE, %s, fecha_hora) <= NOW() AS vencida
                FROM compra
                WHERE id_compra = %s
                """,
                (RESERVA_DURACION_MINUTOS, id_compra)
            )
            vencimiento = cursor.fetchone()

            if vencimiento["vencida"]:
                cursor.execute(
                    "UPDATE compra SET estado = %s WHERE id_compra = %s",
                    (ESTADO_COMPRA_EXPIRADA, id_compra)
                )
                cursor.execute(
                    "UPDATE entrada SET ocupacion_activa = NULL WHERE id_compra = %s",
                    (id_compra,)
                )
                conn.commit()
                return None, {
                    "error": "RESERVA_EXPIRADA",
                    "mensaje": "La reserva ya venció.",
                    "status_code": 409
                }

            cursor.execute(
                "UPDATE compra SET estado = %s WHERE id_compra = %s",
                (ESTADO_COMPRA_RECHAZADA, id_compra)
            )
            cursor.execute(
                "UPDATE entrada SET ocupacion_activa = NULL WHERE id_compra = %s",
                (id_compra,)
            )

            conn.commit()
            return {
                "id_compra": id_compra,
                "estado": ESTADO_COMPRA_RECHAZADA
            }, None

    except mysql.connector.Error:
        if conn is not None:
            conn.rollback()
        return None, {
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudo rechazar la reserva.",
            "status_code": 500
        }

    finally:
        if conn is not None:
            conn.close()


def abandonar_reserva_pendiente(id_compra: int, id_usuario: int):
    conn = None

    try:
        conn = get_connection()
        conn.start_transaction()

        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT id_compra, estado, fecha_hora
                FROM compra
                WHERE id_compra = %s AND id_usuario = %s
                FOR UPDATE
                """,
                (id_compra, id_usuario)
            )
            compra = cursor.fetchone()

            if compra is None:
                conn.rollback()
                return None, {
                    "error": "RESERVA_NO_ENCONTRADA",
                    "mensaje": "No se encontró la reserva.",
                    "status_code": 404
                }

            if compra["estado"] != ESTADO_COMPRA_PENDIENTE:
                conn.rollback()
                return None, {
                    "error": "RESERVA_NO_PENDIENTE",
                    "mensaje": "La reserva no se encuentra pendiente.",
                    "status_code": 409
                }

            cursor.execute(
                """
                SELECT TIMESTAMPADD(MINUTE, %s, fecha_hora) <= NOW() AS vencida
                FROM compra
                WHERE id_compra = %s
                """,
                (RESERVA_DURACION_MINUTOS, id_compra)
            )
            if cursor.fetchone()["vencida"]:
                cursor.execute(
                    "UPDATE compra SET estado = %s WHERE id_compra = %s",
                    (ESTADO_COMPRA_EXPIRADA, id_compra)
                )
                cursor.execute(
                    "UPDATE entrada SET ocupacion_activa = NULL WHERE id_compra = %s",
                    (id_compra,)
                )
                conn.commit()
                return None, {
                    "error": "RESERVA_EXPIRADA",
                    "mensaje": "La reserva ya venció.",
                    "status_code": 409
                }

            cursor.execute(
                "UPDATE compra SET estado = %s WHERE id_compra = %s",
                (ESTADO_COMPRA_CANCELADA, id_compra)
            )
            cursor.execute(
                "UPDATE entrada SET ocupacion_activa = NULL WHERE id_compra = %s",
                (id_compra,)
            )

            conn.commit()
            return {
                "id_compra": id_compra,
                "estado": ESTADO_COMPRA_CANCELADA
            }, None

    except mysql.connector.Error:
        if conn is not None:
            conn.rollback()
        return None, {
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudo abandonar la reserva.",
            "status_code": 500
        }

    finally:
        if conn is not None:
            conn.close()


def editar_reserva_pendiente(id_compra: int, id_usuario: int, lista_id_butacas: list, servicios: list = None):
    if servicios is None:
        servicios = []

    conn = None

    try:
        conn = get_connection()
        conn.start_transaction()

        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT id_compra, estado
                FROM compra
                WHERE id_compra = %s AND id_usuario = %s
                FOR UPDATE
                """,
                (id_compra, id_usuario)
            )
            compra = cursor.fetchone()

            if compra is None:
                conn.rollback()
                return None, {
                    "error": "RESERVA_NO_ENCONTRADA",
                    "mensaje": "No se encontró la reserva.",
                    "status_code": 404
                }

            if compra["estado"] != ESTADO_COMPRA_PENDIENTE:
                conn.rollback()
                return None, {
                    "error": "RESERVA_NO_PENDIENTE",
                    "mensaje": "Solo se pueden editar reservas pendientes.",
                    "status_code": 409
                }

            cursor.execute(
                """
                SELECT TIMESTAMPADD(MINUTE, %s, fecha_hora) <= NOW() AS vencida
                FROM compra
                WHERE id_compra = %s
                """,
                (RESERVA_DURACION_MINUTOS, id_compra)
            )

            if cursor.fetchone()["vencida"]:
                cursor.execute(
                    "UPDATE compra SET estado = %s WHERE id_compra = %s",
                    (ESTADO_COMPRA_EXPIRADA, id_compra)
                )
                cursor.execute(
                    "UPDATE entrada SET ocupacion_activa = NULL WHERE id_compra = %s",
                    (id_compra,)
                )
                conn.commit()
                return None, {
                    "error": "RESERVA_EXPIRADA",
                    "mensaje": "La reserva ya venció.",
                    "status_code": 409
                }

            cursor.execute(
                """
                SELECT id_funcion
                FROM entrada
                WHERE id_compra = %s
                LIMIT 1
                """,
                (id_compra,)
            )
            entrada_actual = cursor.fetchone()

            if entrada_actual is None:
                conn.rollback()
                return None, {
                    "error": "RESERVA_SIN_ENTRADAS",
                    "mensaje": "No se encontraron entradas asociadas a la reserva.",
                    "status_code": 409
                }

            id_funcion = entrada_actual["id_funcion"]
            funcion = obtener_funcion(cursor, id_funcion)

            if funcion is None:
                conn.rollback()
                return None, {
                    "error": "FUNCION_NO_ENCONTRADA",
                    "mensaje": "La función asociada a la reserva no existe.",
                    "status_code": 404
                }

            try:
                validar_inicio_funcion(
                    funcion["fecha_hora_inicio"],
                    obtener_hora_actual(cursor)
                )
            except ValueError as error:
                conn.rollback()
                return None, {
                    "error": "FUNCION_INICIADA",
                    "mensaje": str(error),
                    "status_code": 400
                }

            butacas_sala = obtener_butacas_de_funcion(cursor, id_funcion)
            ids_validos = {butaca["id_butaca"] for butaca in butacas_sala}

            if any(id_butaca not in ids_validos for id_butaca in lista_id_butacas):
                conn.rollback()
                return None, {
                    "error": "BUTACAS_INVALIDAS",
                    "mensaje": "Una o más butacas no pertenecen a la sala de esta función.",
                    "status_code": 400
                }

            placeholders = ",".join(["%s"] * len(lista_id_butacas))
            cursor.execute(
                f"""
                SELECT entrada.id_butaca
                FROM entrada
                JOIN compra ON compra.id_compra = entrada.id_compra
                WHERE entrada.id_funcion = %s
                  AND entrada.id_butaca IN ({placeholders})
                  AND entrada.ocupacion_activa = 1
                  AND entrada.id_compra <> %s
                  AND (
                      compra.estado = %s
                      OR (
                          compra.estado = %s
                          AND TIMESTAMPADD(MINUTE, %s, compra.fecha_hora) > NOW()
                      )
                  )
                FOR UPDATE
                """,
                [id_funcion]
                + lista_id_butacas
                + [
                    id_compra,
                    ESTADO_COMPRA_CONFIRMADA,
                    ESTADO_COMPRA_PENDIENTE,
                    RESERVA_DURACION_MINUTOS,
                ]
            )
            ocupadas = [fila["id_butaca"] for fila in cursor.fetchall()]

            if ocupadas:
                conn.rollback()
                return None, {
                    "error": "BUTACAS_OCUPADAS",
                    "mensaje": "Una o más butacas seleccionadas ya están reservadas o vendidas.",
                    "butacas_conflictivas": ocupadas,
                    "status_code": 409
                }

            total_entradas = Decimal(str(funcion["precio_base"])) * len(lista_id_butacas)
            total_servicios = Decimal("0.00")
            servicios_a_guardar = []

            for servicio in servicios:
                servicio_db = obtener_servicio(cursor, servicio["id_servicio"])

                if servicio_db is None:
                    conn.rollback()
                    return None, {
                        "error": "SERVICIO_NO_ENCONTRADO",
                        "mensaje": f"El servicio {servicio['id_servicio']} no existe.",
                        "status_code": 404
                    }

                precio_unitario = Decimal(str(servicio_db["precio"]))
                cantidad = servicio["cantidad"]
                total_servicios += precio_unitario * cantidad

                servicios_a_guardar.append({
                    "id_servicio": servicio["id_servicio"],
                    "cantidad": cantidad,
                    "precio_unitario": precio_unitario
                })

            cursor.execute(
                "UPDATE entrada SET ocupacion_activa = NULL WHERE id_compra = %s",
                (id_compra,)
            )

            crear_entradas_reserva(
                cursor,
                id_compra,
                id_funcion,
                lista_id_butacas
            )

            cursor.execute(
                "DELETE FROM compra_servicio WHERE id_compra = %s",
                (id_compra,)
            )

            for servicio in servicios_a_guardar:
                agregar_servicio_a_compra(
                    cursor,
                    id_compra,
                    servicio["id_servicio"],
                    servicio["cantidad"],
                    servicio["precio_unitario"]
                )

            total = total_entradas + total_servicios

            cursor.execute(
                "UPDATE compra SET total = %s WHERE id_compra = %s",
                (total, id_compra)
            )

            conn.commit()

            return {
                "id_compra": id_compra,
                "id_funcion": id_funcion,
                "butacas": lista_id_butacas,
                "servicios": servicios_a_guardar,
                "total": float(total),
                "estado": ESTADO_COMPRA_PENDIENTE
            }, None

    except mysql.connector.Error as error:
        if conn is not None:
            conn.rollback()

        if error.errno == 1062:
            return None, {
                "error": "BUTACAS_OCUPADAS",
                "mensaje": "Una o más butacas seleccionadas ya están reservadas o vendidas.",
                "status_code": 409
            }

        if error.errno in (1205, 1213):
            return None, {
                "error": "CONFLICTO_RESERVA",
                "mensaje": "Otra operación está modificando la reserva. Volvé a intentar.",
                "status_code": 409
            }

        return None, {
            "error": "ERROR_BASE_DATOS",
            "mensaje": "No se pudo editar la reserva.",
            "status_code": 500
        }

    finally:
        if conn is not None:
            conn.close()
