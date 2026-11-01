import mysql.connector
from mysql.connector import Error
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
app = Flask(__name__)
app.json.sort_keys = False 
load_dotenv()


DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}



def ejecutar_guardar(query, valores):
    """Ejecuta consultas de escritura (INSERT, UPDATE, DELETE) y confirma cambios."""
    conexion = None
    cursor = None
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        if conexion.is_connected():
            cursor = conexion.cursor()
            cursor.execute(query, valores)
            conexion.commit() # Guarda los cambios en la BD
            return {
                "exito": True, 
                "mensaje": "Operación realizada y guardada correctamente."
            }
    
    except Error as e:
        return {
            "exito": False, 
            "mensaje": f"Error crítico al guardar en la base de datos: {e}"


        }
    finally:
        if cursor: cursor.close()
        if conexion and conexion.is_connected(): conexion.close()


def ejecutar_buscar(query, valores=None):
    """Ejecuta consultas de lectura (SELECT) y devuelve las filas encontradas."""
    conexion = None
    cursor = None
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        if conexion.is_connected():
            # dictionary=True hace que los resultados vengan como {'columna': valor}
            cursor = conexion.cursor(dictionary=True) 
            cursor.execute(query, valores)
            resultados = cursor.fetchall() # Trae todas las filas de la búsqueda
            return {
                "exito": True, 
                "datos": resultados,
                "mensaje": f"Se encontraron {len(resultados)} registros."
            }
    except Error as e:
        return {
            "exito": False, 
            "datos": [],
            "mensaje": f"Error crítico al buscar en la base de datos: {e}"
        }
    finally:
        if cursor: cursor.close()
        if conexion and conexion.is_connected(): conexion.close()
