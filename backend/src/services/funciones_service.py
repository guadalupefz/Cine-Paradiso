from backend.db.db import get_connection
from backend.src.repositories.funciones_repository import (obtener_funciones, 
                                                           crear_funcion, 
                                                           contar_entradas_por_funcion, 
                                                           verificar_solapamiento_sala)

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
    cursor = conn.cursor(dictionary=True)
    
    try:
        id_pelicula = data.get('id_pelicula')
        id_sala = data.get('id_sala')
        fecha_hora_inicio = data.get('fecha_hora_inicio')
        precio_base = data.get('precio_base')
        cursor.execute("SELECT duracion_minutos FROM pelicula WHERE id_pelicula = %s", (id_pelicula,))
        peli = cursor.fetchone()

        if not peli:
            raise ValueError("La película especificada no existe.")
            
        duracion_str = "".join(filter(str.isdigit, str(peli["duracion_minutos"])))
        duracion_minutos = int(duracion_str) if duracion_str else 120

        if verificar_solapamiento_sala(cursor, id_sala, fecha_hora_inicio, duracion_minutos):
            raise ValueError("La sala ya se encuentra ocupada en ese rango horario por otra función.")

        nuevo_id = crear_funcion(cursor, id_pelicula, id_sala, fecha_hora_inicio, precio_base)
        conn.commit()

        return nuevo_id
        
    except Exception as e:
        conn.rollback()
        raise e
        
    finally:
        cursor.close()
        conn.close()