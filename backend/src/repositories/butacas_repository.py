def obtener_butacas_por_funcion(cursor, id_funcion):
    query = """
        SELECT
            butaca.id_butaca,
            butaca.fila,
            butaca.numero,
            CASE
                WHEN compra.estado IN ('aprobada', 'confirmada')
                    THEN 'ocupada'
                WHEN compra.estado = 'pendiente'
                    AND compra.fecha_hora > NOW() - INTERVAL 15 MINUTE
                    THEN 'reservada'
                ELSE 'disponible'
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
    cursor.execute(query, (id_funcion,))
    return cursor.fetchall()
