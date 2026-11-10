from backend.src.constants import (
    ESTADO_BUTACA_DISPONIBLE,
    ESTADO_BUTACA_OCUPADA,
    ESTADO_BUTACA_RESERVADA,
    ESTADO_COMPRA_CONFIRMADA,
    ESTADO_COMPRA_PENDIENTE,
    RESERVA_DURACION_MINUTOS,
)


def obtener_butacas_por_funcion(cursor, id_funcion):
    query = """
        SELECT
            butaca.id_butaca,
            butaca.fila,
            butaca.numero,
            CASE
                WHEN compra.estado = %s
                    THEN %s
                WHEN compra.estado = %s
                    AND TIMESTAMPADD(MINUTE, %s, compra.fecha_hora) > NOW()
                    THEN %s
                ELSE %s
            END AS estado
        FROM funcion
        JOIN sala ON funcion.id_sala = sala.id_sala
        JOIN butaca ON sala.id_sala = butaca.id_sala
        LEFT JOIN entrada
            ON entrada.id_funcion = funcion.id_funcion
            AND entrada.id_butaca = butaca.id_butaca
            AND entrada.ocupacion_activa = 1
        LEFT JOIN compra
            ON compra.id_compra = entrada.id_compra
        WHERE funcion.id_funcion = %s
        ORDER BY butaca.fila, butaca.numero
    """
    cursor.execute(
        query,
        (
            ESTADO_COMPRA_CONFIRMADA,
            ESTADO_BUTACA_OCUPADA,
            ESTADO_COMPRA_PENDIENTE,
            RESERVA_DURACION_MINUTOS,
            ESTADO_BUTACA_RESERVADA,
            ESTADO_BUTACA_DISPONIBLE,
            id_funcion,
        ),
    )
    return cursor.fetchall()
