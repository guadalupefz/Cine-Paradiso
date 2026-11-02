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
            return {"exito": True, "datos": filas}
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
            return {"exito": True, "id": id_creado}
        except mysql.connector.Error:
            conexion.rollback()
            raise
        finally:
            conexion.close()
    except mysql.connector.Error:
        return {"exito": False, "mensaje": "No se pudo guardar en MySQL."}
