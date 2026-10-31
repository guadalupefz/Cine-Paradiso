from src.db import get_connection
from src.repositories.funciones import (obtener_funciones,
                                        crear_funcion)

#Devuelve lista de diccionarios
def listar_funciones_servicio():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        funciones = obtener_funciones(cursor)
        return funciones

    finally:
        cursor.close()
        conn.close()

#Devuelve nuevo ID
def crear_funcion_servicio(data):
   
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        id_pelicula = data.get('id_pelicula')
        id_sala = data.get('id_sala')
        fecha_hora_inicio = data.get('fecha_hora_inicio')
        precio_base = data.get('precio_base')

        nuevo_id = crear_funcion(cursor, id_pelicula, id_sala, fecha_hora_inicio, precio_base)
        conn.commit()

        return nuevo_id
        
    except Exception as e:
        conn.rollback()
        raise e
        
    finally:
        cursor.close()
        conn.close()