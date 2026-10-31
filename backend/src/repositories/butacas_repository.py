# Obtener las butacas de una función y su estado de ocupación
def obtener_butacas_por_funcion(cursor, id_funcion):
    query = """
        SELECT
            b.id_butaca,
            b.fila,
            b.numero,
            CASE
                WHEN e.id_entrada IS NOT NULL THEN 'ocupada'
                ELSE 'disponible'
            END AS estado
        FROM funcion f
        JOIN sala s ON f.id_sala = s.id_sala
        JOIN butaca b ON s.id_sala = b.id_sala
        LEFT JOIN entrada e
            ON e.id_funcion = f.id_funcion
            AND e.id_butaca = b.id_butaca
        WHERE f.id_funcion = %s
        ORDER BY b.fila, b.numero
    """
    cursor.execute(query, (id_funcion,))
    return cursor.fetchall()