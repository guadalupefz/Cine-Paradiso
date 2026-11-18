import uuid
from decimal import Decimal

from backend.src.constants import (
    ESTADO_COMPRA_CONFIRMADA,
    ESTADO_COMPRA_EXPIRADA,
    ESTADO_COMPRA_PENDIENTE,
    RESERVA_DURACION_MINUTOS,
)


def obtener_butacas_ocupadas_con_bloqueo(cursor, id_funcion, lista_id_butacas):
    placeholders = ",".join(["%s"] * len(lista_id_butacas))

    query = f"""
        SELECT entrada.id_butaca
        FROM entrada
        JOIN compra ON entrada.id_compra = compra.id_compra
        WHERE entrada.id_funcion = %s
          AND entrada.id_butaca IN ({placeholders})
          AND entrada.ocupacion_activa = 1
          AND (
                compra.estado = %s
                OR (
                    compra.estado = %s
                    AND TIMESTAMPADD(MINUTE, %s, compra.fecha_hora) > NOW()
                )
            )
        FOR UPDATE
    """

    parametros = (
        [id_funcion]
        + list(lista_id_butacas)
        + [
            ESTADO_COMPRA_CONFIRMADA,
            ESTADO_COMPRA_PENDIENTE,
            RESERVA_DURACION_MINUTOS,
        ]
    )
    cursor.execute(query, parametros)

    filas = cursor.fetchall()
    return [fila["id_butaca"] for fila in filas]


def limpiar_reservas_expiradas(cursor, id_funcion):
    query = """
        UPDATE entrada
        JOIN compra ON entrada.id_compra = compra.id_compra
        SET compra.estado = %s,
            entrada.ocupacion_activa = NULL
        WHERE entrada.id_funcion = %s
          AND compra.estado = %s
          AND TIMESTAMPADD(MINUTE, %s, compra.fecha_hora) <= NOW()
    """

    cursor.execute(
        query,
        (
            ESTADO_COMPRA_EXPIRADA,
            id_funcion,
            ESTADO_COMPRA_PENDIENTE,
            RESERVA_DURACION_MINUTOS,
        ),
    )


def obtener_precio_base_funcion(cursor, id_funcion: int):
    query = "SELECT precio_base FROM funcion WHERE id_funcion = %s FOR UPDATE;"
    cursor.execute(query, (id_funcion,))
    res = cursor.fetchone()
    return res['precio_base'] if res else None

def crear_compra_pendiente(
    cursor, id_usuario: int, total: Decimal, fecha_hora_creacion
):
    query = """
        INSERT INTO compra (id_usuario, fecha_hora, total, estado)
        VALUES (%s, %s, %s, %s);
    """
    cursor.execute(
        query,
        (id_usuario, fecha_hora_creacion, total, ESTADO_COMPRA_PENDIENTE),
    )
    return cursor.lastrowid

def crear_entradas_reserva(cursor, id_compra: int, id_funcion: int, lista_id_butacas: list):
    datos = []
    for id_b in lista_id_butacas:
        token_temp = f"PENDING-{id_compra}-{id_b}-{uuid.uuid4().hex[:6]}"
        datos.append((id_compra, id_funcion, id_b, token_temp))

    query = """
        INSERT INTO entrada (id_compra, id_funcion, id_butaca, qr_token)
        VALUES (%s, %s, %s, %s);
    """
    cursor.executemany(query, datos)

def agregar_servicio_a_compra(
    cursor, id_compra, id_servicio, cantidad, precio_unitario
):
    query = """
        INSERT INTO compra_servicio
            (id_compra, id_servicio, cantidad, precio_unitario)
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (id_compra, id_servicio, cantidad, precio_unitario)
    )


def obtener_compra_reserva_para_actualizar(cursor, id_compra, id_usuario):
    cursor.execute(
        """
        SELECT id_compra, estado, fecha_hora
        FROM compra
        WHERE id_compra = %s AND id_usuario = %s
        FOR UPDATE
        """,
        (id_compra, id_usuario),
    )
    return cursor.fetchone()


def reserva_vencida(cursor, id_compra):
    cursor.execute(
        """
        SELECT TIMESTAMPADD(MINUTE, %s, fecha_hora) <= NOW() AS vencida
        FROM compra
        WHERE id_compra = %s
        """,
        (RESERVA_DURACION_MINUTOS, id_compra),
    )
    resultado = cursor.fetchone()
    return bool(resultado and resultado["vencida"])


def actualizar_estado_compra(cursor, id_compra, estado):
    cursor.execute(
        "UPDATE compra SET estado = %s WHERE id_compra = %s",
        (estado, id_compra),
    )


def liberar_entradas_reserva(cursor, id_compra):
    cursor.execute(
        "UPDATE entrada SET ocupacion_activa = NULL WHERE id_compra = %s",
        (id_compra,),
    )


def obtener_funcion_de_reserva(cursor, id_compra):
    cursor.execute(
        """
        SELECT id_funcion
        FROM entrada
        WHERE id_compra = %s
        LIMIT 1
        """,
        (id_compra,),
    )
    return cursor.fetchone()


def obtener_butacas_ocupadas_para_edicion(
    cursor, id_funcion, lista_id_butacas, id_compra
):
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
        + list(lista_id_butacas)
        + [
            id_compra,
            ESTADO_COMPRA_CONFIRMADA,
            ESTADO_COMPRA_PENDIENTE,
            RESERVA_DURACION_MINUTOS,
        ],
    )
    return [fila["id_butaca"] for fila in cursor.fetchall()]


def eliminar_entradas_reserva(cursor, id_compra):
    cursor.execute(
        "DELETE FROM entrada WHERE id_compra = %s",
        (id_compra,),
    )


def eliminar_servicios_reserva(cursor, id_compra):
    cursor.execute(
        "DELETE FROM compra_servicio WHERE id_compra = %s",
        (id_compra,),
    )


def actualizar_total_compra(cursor, id_compra, total):
    cursor.execute(
        "UPDATE compra SET total = %s WHERE id_compra = %s",
        (total, id_compra),
    )
