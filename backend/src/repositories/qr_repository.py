def validar_entrada(cursor, qr_token):
    query = """
        SELECT entrada.*, compra.estado AS estado_compra,
               funcion.fecha_hora_inicio
        FROM entrada
        JOIN compra ON entrada.id_compra = compra.id_compra
        JOIN funcion ON entrada.id_funcion = funcion.id_funcion
        WHERE entrada.qr_token = %s
        FOR UPDATE
    """

    cursor.execute(query, (qr_token,))

    return cursor.fetchone()

def marcar_entrada_usada(cursor, id_entrada):
    query = """
        UPDATE entrada
        SET fecha_hora_validacion = NOW()
        WHERE id_entrada = %s
          AND fecha_hora_validacion IS NULL
    """

    cursor.execute(query, (id_entrada,))

    return cursor.rowcount

def obtener_entrada_para_qr(cursor, id_entrada, id_usuario):
    query = """
        SELECT entrada.qr_token
        FROM entrada
        JOIN compra ON entrada.id_compra = compra.id_compra
        WHERE entrada.id_entrada = %s
        AND compra.id_usuario = %s
    """

    cursor.execute(query, (id_entrada, id_usuario))
    return cursor.fetchone()

    