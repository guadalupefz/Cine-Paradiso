import mysql.connector

from backend.db.db import get_connection
from backend.src.repositories import locales_repository as locales
from backend.src.repositories import salas_repository as salas


def eliminar_estructura(tipo, identificador):
    """Elimina salas o locales sin actividad y su configuración en una transacción."""
    if tipo not in ("local", "sala"):
        raise ValueError("Tipo de estructura inválido")
    if identificador <= 0:
        return {"error": "El ID debe ser positivo."}, 400

    conexion = None
    try:
        conexion = get_connection()
        with conexion.cursor(dictionary=True) as cursor:
            # El bloqueo impide crear dependencias mientras se verifica y elimina.
            if tipo == "local":
                elemento = locales.bloquear_local(cursor, identificador)
                if elemento is not None:
                    locales.bloquear_salas_del_local(cursor, identificador)
                    en_uso = locales.local_en_uso(cursor, identificador)
            else:
                elemento = salas.bloquear_sala(cursor, identificador)
                if elemento is not None:
                    en_uso = salas.sala_en_uso(cursor, identificador)

            if elemento is None:
                conexion.rollback()
                return {"error": "El local o la sala indicados no existen."}, 404
            if en_uso:
                conexion.rollback()
                return {"error": "No se puede eliminar: hay funciones o entradas asociadas."}, 409

            if tipo == "local":
                eliminados = locales.eliminar_local_salas_y_butacas(cursor, identificador)
            else:
                eliminados = salas.eliminar_sala_y_butacas(cursor, identificador)
            if eliminados != 1:
                conexion.rollback()
                return {"error": "No se pudo completar la eliminación. Volvé a cargar la página."}, 409

        conexion.commit()
        mensaje = "Local eliminado junto con sus salas y butacas." if tipo == "local" else "Sala eliminada junto con sus butacas."
        return {"mensaje": mensaje}, 200
    except mysql.connector.IntegrityError:
        if conexion is not None:
            conexion.rollback()
        return {"error": "No se puede eliminar: existen registros asociados que deben conservarse."}, 409
    except mysql.connector.Error as error:
        if conexion is not None:
            conexion.rollback()
        if error.errno in (1205, 1213):
            return {"error": "El registro está siendo utilizado. Intentá nuevamente."}, 409
        return {"error": "No se pudo eliminar el registro."}, 500
    finally:
        if conexion is not None:
            conexion.close()
