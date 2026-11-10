from backend.src.constants import (
    ESTADO_COMPRA_CANCELADA,
    ESTADO_COMPRA_CONFIRMADA,
)


def obtener_ventas_por_genero(cursor, desde=None, hasta=None):
    filtros = ["LOWER(c.estado) = %s"]
    parametros = [ESTADO_COMPRA_CONFIRMADA]

    if desde:
        filtros.append("f.fecha_hora_inicio >= %s")
        parametros.append(desde)

    if hasta:
        filtros.append(
            "f.fecha_hora_inicio < DATE_ADD(%s, INTERVAL 1 DAY)"
        )
        parametros.append(hasta)

    query = f"""
        SELECT
            datos.genero,
            SUM(datos.entradas_vendidas) AS entradas_vendidas,
            COALESCE(SUM(datos.importe_entradas), 0)
                AS importe_estimado_entradas
        FROM (
            SELECT
                c.id_compra,
                p.genero,
                COUNT(e.id_entrada) AS entradas_vendidas,
                c.total - (
                    SELECT COALESCE(
                        SUM(cs.cantidad * cs.precio_unitario), 0
                    )
                    FROM compra_servicio cs
                    WHERE cs.id_compra = c.id_compra
                ) AS importe_entradas
            FROM entrada e
            JOIN compra c ON c.id_compra = e.id_compra
            JOIN funcion f ON f.id_funcion = e.id_funcion
            JOIN pelicula p ON p.id_pelicula = f.id_pelicula
            WHERE {" AND ".join(filtros)}
            GROUP BY
                c.id_compra,
                p.genero,
                c.total
        ) AS datos
        GROUP BY datos.genero
        ORDER BY entradas_vendidas DESC
    """

    cursor.execute(query, tuple(parametros))
    return cursor.fetchall()


def obtener_ventas_por_franja(cursor, desde=None, hasta=None):
    filtros = ["LOWER(c.estado) = %s"]
    parametros = [ESTADO_COMPRA_CONFIRMADA]

    if desde:
        filtros.append("f.fecha_hora_inicio >= %s")
        parametros.append(desde)

    if hasta:
        filtros.append(
            "f.fecha_hora_inicio < DATE_ADD(%s, INTERVAL 1 DAY)"
        )
        parametros.append(hasta)

    query = f"""
        SELECT
            datos.franja_horaria,
            SUM(datos.entradas_vendidas) AS entradas_vendidas,
            COALESCE(SUM(datos.importe_entradas), 0)
                AS importe_estimado_entradas
        FROM (
            SELECT
                c.id_compra,
                CASE
                    WHEN HOUR(f.fecha_hora_inicio) < 12 THEN 'Mañana'
                    WHEN HOUR(f.fecha_hora_inicio) < 18 THEN 'Tarde'
                    ELSE 'Noche'
                END AS franja_horaria,
                COUNT(e.id_entrada) AS entradas_vendidas,
                c.total - (
                    SELECT COALESCE(
                        SUM(cs.cantidad * cs.precio_unitario), 0
                    )
                    FROM compra_servicio cs
                    WHERE cs.id_compra = c.id_compra
                ) AS importe_entradas
            FROM entrada e
            JOIN compra c ON c.id_compra = e.id_compra
            JOIN funcion f ON f.id_funcion = e.id_funcion
            WHERE {" AND ".join(filtros)}
            GROUP BY
                c.id_compra,
                franja_horaria,
                c.total
        ) AS datos
        GROUP BY datos.franja_horaria
        ORDER BY entradas_vendidas DESC
    """

    cursor.execute(query, tuple(parametros))
    return cursor.fetchall()


def obtener_ocupacion_por_funcion(cursor, desde=None, hasta=None):
    filtros = []
    parametros = [ESTADO_COMPRA_CONFIRMADA, ESTADO_COMPRA_CONFIRMADA]

    if desde:
        filtros.append("f.fecha_hora_inicio >= %s")
        parametros.append(desde)

    if hasta:
        filtros.append(
            "f.fecha_hora_inicio < DATE_ADD(%s, INTERVAL 1 DAY)"
        )
        parametros.append(hasta)

    where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

    query = f"""
        SELECT
            f.id_funcion,
            p.titulo AS pelicula,
            f.fecha_hora_inicio,
            s.nombre AS sala,
            s.capacidad,
            COUNT(DISTINCT CASE
                WHEN LOWER(c.estado) = %s
                THEN e.id_butaca
            END) AS butacas_ocupadas,
            ROUND(
                100.0 * COUNT(DISTINCT CASE
                    WHEN LOWER(c.estado) = %s
                    THEN e.id_butaca
                END) / NULLIF(s.capacidad, 0),
                2
            ) AS porcentaje_ocupacion
        FROM funcion f
        JOIN pelicula p ON p.id_pelicula = f.id_pelicula
        JOIN sala s ON s.id_sala = f.id_sala
        LEFT JOIN entrada e ON e.id_funcion = f.id_funcion
        LEFT JOIN compra c ON c.id_compra = e.id_compra
        {where}
        GROUP BY
            f.id_funcion,
            p.titulo,
            f.fecha_hora_inicio,
            s.nombre,
            s.capacidad
        ORDER BY f.fecha_hora_inicio
    """

    cursor.execute(query, tuple(parametros))
    return cursor.fetchall()


def obtener_ocupacion_por_pelicula(cursor, desde=None, hasta=None):
    filtros = []
    parametros = [ESTADO_COMPRA_CONFIRMADA]

    if desde:
        filtros.append("f.fecha_hora_inicio >= %s")
        parametros.append(desde)

    if hasta:
        filtros.append(
            "f.fecha_hora_inicio < DATE_ADD(%s, INTERVAL 1 DAY)"
        )
        parametros.append(hasta)

    where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

    query = f"""
        SELECT
            datos.id_pelicula,
            datos.pelicula,
            SUM(datos.capacidad) AS capacidad_total,
            SUM(datos.butacas_ocupadas) AS butacas_ocupadas,
            ROUND(
                100.0 * SUM(datos.butacas_ocupadas)
                / NULLIF(SUM(datos.capacidad), 0),
                2
            ) AS porcentaje_ocupacion
        FROM (
            SELECT
                f.id_funcion,
                p.id_pelicula,
                p.titulo AS pelicula,
                s.capacidad,
                COUNT(DISTINCT CASE
                    WHEN LOWER(c.estado) = %s
                    THEN e.id_butaca
                END) AS butacas_ocupadas
            FROM funcion f
            JOIN pelicula p ON p.id_pelicula = f.id_pelicula
            JOIN sala s ON s.id_sala = f.id_sala
            LEFT JOIN entrada e ON e.id_funcion = f.id_funcion
            LEFT JOIN compra c ON c.id_compra = e.id_compra
            {where}
            GROUP BY
                f.id_funcion,
                p.id_pelicula,
                p.titulo,
                s.capacidad
        ) AS datos
        GROUP BY datos.id_pelicula, datos.pelicula
        ORDER BY porcentaje_ocupacion DESC
    """

    cursor.execute(query, tuple(parametros))
    return cursor.fetchall()


def obtener_cantidad_cancelaciones(cursor):
    query = """
        SELECT COUNT(*) AS cantidad_cancelaciones
        FROM compra
        WHERE LOWER(estado) = %s
    """

    cursor.execute(query, (ESTADO_COMPRA_CANCELADA,))
    return cursor.fetchone()
