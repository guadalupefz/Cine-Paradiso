"""Conexion compartida y ejecucion usada por el importador de peliculas."""
import mysql.connector
from backend.db.db import get_connection

def ejecutar_buscar(query, valores=None):
    try:
        conexion = get_connection()
        try:
            with conexion.cursor(dictionary=True) as cursor:
                cursor.execute(query, valores)
                filas = cursor.fetchall()
            return {"exito": True, "datos": filas, "mensaje": f"Se encontraron {len(filas)} registros."}
        finally:
            conexion.close()
    except mysql.connector.Error:
        return {"exito": False, "datos": [], "mensaje": "No se pudo consultar MySQL."}

def ejecutar_guardar(query, valores):
    try:
        conexion = get_connection()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(query, valores)
                id_creado = cursor.lastrowid
            conexion.commit()
            return {"exito": True, "id": id_creado, "mensaje": "Operación realizada y guardada correctamente."}
        except mysql.connector.Error:
            conexion.rollback()
            raise
        finally:
            conexion.close()
    except mysql.connector.Error:
        return {"exito": False, "mensaje": "No se pudo guardar en MySQL."}


def ejecutar_buscar_uno(query, valores=None):
    """Devuelve la primera fila y mantiene el contrato de los ayudantes SQL."""
    try:
        conexion = get_connection()
        try:
            # El buffer consume el resultado completo aunque solo se devuelva
            # una fila: cerrar el cursor no deja resultados pendientes.
            with conexion.cursor(dictionary=True, buffered=True) as cursor:
                cursor.execute(query, valores)
                fila = cursor.fetchone()
            mensaje = "Registro encontrado con éxito." if fila is not None else "No se encontró ningún registro que coincida."
            return {"exito": True, "datos": fila, "mensaje": mensaje}
        finally:
            conexion.close()
    except mysql.connector.Error:
        return {"exito": False, "datos": None, "mensaje": "No se pudo consultar MySQL."}
