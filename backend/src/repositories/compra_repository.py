def obtener_funcion(cursor, id_funcion):
    query = """
        SELECT id_funcion, id_sala, precio_base, fecha_hora_inicio
        FROM funcion
        WHERE id_funcion = %s
        FOR UPDATE
    """
    cursor.execute(query, (id_funcion,))
    return cursor.fetchone()

def obtener_usuario(cursor, id_usuario):
    query = """
        SELECT id_usuario
        FROM usuario
        WHERE id_usuario = %s
    """
    cursor.execute(query, (id_usuario,))
    return cursor.fetchone()

def obtener_butacas_de_funcion(cursor, id_funcion):
    query = """
        SELECT b.id_butaca
        FROM funcion f
        JOIN butaca b ON b.id_sala = f.id_sala
        WHERE f.id_funcion = %s
    """
    cursor.execute(query, (id_funcion,))
    return cursor.fetchall()


def obtener_butacas_ocupadas(cursor, id_funcion):
    query = """
        SELECT id_butaca
        FROM entrada
        WHERE id_funcion = %s
        FOR UPDATE
    """
    cursor.execute(query, (id_funcion,))
    return cursor.fetchall()


def crear_compra(cursor, id_usuario, total, estado):
    query = """
        INSERT INTO compra (id_usuario, total, estado)
        VALUES (%s, %s, %s)
    """
    cursor.execute(query, (id_usuario, total, estado))
    return cursor.lastrowid


def crear_entrada(cursor, id_compra, id_funcion, id_butaca, qr_token):
    query = """
        INSERT INTO entrada (id_compra, id_funcion, id_butaca, qr_token)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (id_compra, id_funcion, id_butaca, qr_token))
    return cursor.lastrowid


def obtener_compra_por_id(cursor, id_compra):
    query = """
        SELECT id_compra, id_usuario, fecha_hora, total, estado
        FROM compra
        WHERE id_compra = %s
    """
    cursor.execute(query, (id_compra,))
    return cursor.fetchone()


def obtener_entradas_por_compra(cursor, id_compra):
    query = """
        SELECT
            entrada.id_entrada,
            entrada.id_funcion,
            entrada.id_butaca,
            entrada.qr_token,
            entrada.fecha_hora_validacion,
            butaca.fila,
            butaca.numero
        FROM entrada
        INNER JOIN butaca
            ON entrada.id_butaca = butaca.id_butaca
        WHERE entrada.id_compra = %s
    """
    cursor.execute(query, (id_compra,))
    return cursor.fetchall()


def obtener_compras_por_usuario(cursor, id_usuario):
    consulta = """
        SELECT id_compra, fecha_hora, total, estado
        FROM compra
        WHERE id_usuario = %s
    """
    cursor.execute(consulta, (id_usuario,))
    return cursor.fetchall()

def obtener_servicios_de_compra(cursor, id_compra):
    consulta = """
        SELECT cs.id_servicio, sa.nombre, cs.cantidad, cs.precio_unitario, cs.cantidad * cs.precio_unitario AS subtotal
        FROM compra_servicio AS cs
        INNER JOIN servicio_adicional AS sa
        ON cs.id_servicio = sa.id_servicio
        WHERE cs.id_compra = %s
    """
    cursor.execute(consulta, (id_compra,))
    return cursor.fetchall()

def obtener_compra_de_usuario(cursor, id_compra, id_usuario):
    consulta = """
        SELECT id_compra, fecha_hora, total, estado
        FROM compra
        WHERE id_compra = %s AND id_usuario = %s
    """
    cursor.execute(consulta, (id_compra, id_usuario))
    return cursor.fetchone()

def obtener_datos_comprobante(cursor, id_compra, id_usuario):
    query = """
        SELECT compra.id_compra, compra.fecha_hora,compra.total, compra.estado,
            usuario.nombre, usuario.apellido, usuario.email
        FROM compra
        JOIN usuario ON compra.id_usuario = usuario.id_usuario
        WHERE compra.id_compra = %s
          AND compra.id_usuario = %s
    """

    cursor.execute(query, (id_compra, id_usuario))

    return cursor.fetchone()

def obtener_entradas_comprobante(cursor, id_compra):
    query = """
        SELECT entrada.id_entrada, entrada.id_butaca,
            butaca.fila, butaca.numero,
            funcion.fecha_hora_inicio,
            pelicula.titulo AS pelicula,
            sala.nombre AS sala,
            local.nombre AS local, local.direccion
        FROM entrada
        JOIN funcion ON entrada.id_funcion = funcion.id_funcion
        JOIN pelicula ON funcion.id_pelicula = pelicula.id_pelicula
        JOIN butaca ON entrada.id_butaca = butaca.id_butaca
        JOIN sala ON funcion.id_sala = sala.id_sala
        JOIN local ON sala.id_local = local.id_local
        WHERE entrada.id_compra = %s
        ORDER BY entrada.id_entrada
    """

    cursor.execute(query, (id_compra,))

    return cursor.fetchall()

def obtener_hora_actual(cursor):
    # Se consulta después de adquirir los bloqueos de la operación.
    cursor.execute("SELECT NOW() AS ahora")
    return cursor.fetchone()["ahora"]


def obtener_inicio_funciones_compra(cursor, id_compra):
    cursor.execute(
        """
        SELECT MIN(f.fecha_hora_inicio) AS primer_inicio
        FROM entrada e
        JOIN funcion f ON f.id_funcion = e.id_funcion
        WHERE e.id_compra = %s
        """,
        (id_compra,),
    )
    return cursor.fetchone()["primer_inicio"]
