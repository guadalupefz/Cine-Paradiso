import uuid
from decimal import Decimal

def obtener_butacas_ocupadas_con_bloqueo(cursor, id_funcion: int, lista_id_butacas: list):

    format_strings = ','.join(['%s'] * len(lista_id_butacas))
    query = f"""
        SELECT e.id_butaca
        FROM entrada e
        INNER JOIN compra c ON c.id_compra = e.id_compra
        WHERE e.id_funcion = %s
            AND e.id_butaca IN ({format_strings})
            AND (
                c.estado = 'confirmada'
                OR (c.estado = 'pendiente' AND c.fecha_hora > NOW() - INTERVAL 15 MINUTE)
            )
        FOR UPDATE;
    """
    params = [id_funcion] + list(lista_id_butacas)
    cursor.execute(query, params)
    filas = cursor.fetchall()
    return [fila['id_butaca'] for fila in filas]

def limpiar_reservas_expiradas(cursor, id_funcion: int, lista_id_butacas: list):

    format_strings = ','.join(['%s'] * len(lista_id_butacas))

    query_upd = f"""
        UPDATE compra c
        INNER JOIN entrada e ON e.id_compra = c.id_compra
        SET c.estado = 'expirada'
        WHERE e.id_funcion = %s
            AND e.id_butaca IN ({format_strings})
            AND c.estado = 'pendiente'
            AND c.fecha_hora <= NOW() - INTERVAL 15 MINUTE;
    """
    cursor.execute(query_upd, [id_funcion] + list(lista_id_butacas))

    query_del = f"""
        DELETE e FROM entrada e
        INNER JOIN compra c ON c.id_compra = e.id_compra
        WHERE e.id_funcion = %s
            AND e.id_butaca IN ({format_strings})
            AND c.estado = 'expirada';
    """
    cursor.execute(query_del, [id_funcion] + list(lista_id_butacas))

def obtener_precio_base_funcion(cursor, id_funcion: int):
    query = "SELECT precio_base FROM funcion WHERE id_funcion = %s;"
    cursor.execute(query, (id_funcion,))
    res = cursor.fetchone()
    return res['precio_base'] if res else None

def crear_compra_pendiente(cursor, id_usuario: int, total: Decimal):
    query = """
        INSERT INTO compra (id_usuario, fecha_hora, total, estado)
        VALUES (%s, NOW(), %s, 'pendiente');
    """
    cursor.execute(query, (id_usuario, total))
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
