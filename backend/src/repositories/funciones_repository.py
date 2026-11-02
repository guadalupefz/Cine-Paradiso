from datetime import datetime, timedelta
from backend.src.validators.duracion_validator import minutos_de_duracion

# Consultar la cartelera vigente
def obtener_cartelera(cursor):
    query = """
        SELECT p.id_pelicula, p.titulo, p.sinopsis, p.poster,
               p.duracion_minutos, p.clasificacion, p.genero,
               f.id_funcion, f.fecha_hora_inicio, f.precio_base,
               s.id_sala, s.nombre AS sala_nombre,
               l.nombre AS local_nombre
        FROM funcion f
        JOIN pelicula p ON f.id_pelicula = p.id_pelicula
        JOIN sala s ON f.id_sala = s.id_sala
        JOIN local l ON s.id_local = l.id_local
        WHERE f.fecha_hora_inicio >= NOW()
    """
    cursor.execute(query)
    return cursor.fetchall()

# Listar todas las funciones disponibles
def obtener_funciones(cursor):
    query = """
        SELECT f.id_funcion, f.id_pelicula, f.id_sala, f.fecha_hora_inicio, f.precio_base, p.titulo, s.nombre as sala_nombre
        FROM funcion f
        JOIN pelicula p ON f.id_pelicula = p.id_pelicula
        JOIN sala s ON f.id_sala = s.id_sala
    """
    cursor.execute(query)
    return cursor.fetchall()

# Crear una nueva función (Administrador)
def crear_funcion(cursor, id_pelicula, id_sala, fecha_hora_inicio, precio_base):
    query = "INSERT INTO funcion (id_pelicula, id_sala, fecha_hora_inicio, precio_base) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (id_pelicula, id_sala, fecha_hora_inicio, precio_base))
    return cursor.lastrowid   #Devuelve el ultimo id creado

# Modificar una función existente (Administrador)
def modificar_funcion(cursor, funcion_id, id_pelicula, id_sala, fecha_hora_inicio, precio_base):
    query = """
        UPDATE funcion
        SET id_pelicula = %s, id_sala = %s, fecha_hora_inicio = %s, precio_base = %s
        WHERE id_funcion = %s
    """
    cursor.execute(query, (id_pelicula, id_sala, fecha_hora_inicio, precio_base, funcion_id))
    return cursor.rowcount   #Devuelve la cantidad de filas modificadas

# Verificar entradas vendidas para una función
def contar_entradas_por_funcion(cursor, id_funcion):
    query = "SELECT COUNT(*) as total FROM entrada WHERE id_funcion = %s"
    cursor.execute(query, (id_funcion,))
    resultado = cursor.fetchone()
    return resultado["total"] if isinstance(resultado, dict) else resultado[0]

# Comprobar solapamiento de horarios en una sala
def verificar_solapamiento_sala(cursor, id_sala, fecha_hora_inicio, duracion_nueva_minutos, id_funcion_excluir=None):
    
    query = """
        SELECT f.id_funcion, f.fecha_hora_inicio, p.duracion_minutos
        FROM funcion f
        JOIN pelicula p ON f.id_pelicula = p.id_pelicula
        WHERE f.id_sala = %s
    """
    params = [id_sala]
    
    if id_funcion_excluir:
        query += " AND f.id_funcion != %s"
        params.append(id_funcion_excluir)
        
    cursor.execute(query, tuple(params))
    funciones_existentes = cursor.fetchall()
    
    if isinstance(fecha_hora_inicio, str):
        inicio_nueva = datetime.fromisoformat(fecha_hora_inicio.replace(" ", "T"))
    else:
        inicio_nueva = fecha_hora_inicio
        
    fin_nueva = inicio_nueva + timedelta(minutes=int(duracion_nueva_minutos))
    
    for func in funciones_existentes:
        inicio_existente = func["fecha_hora_inicio"]
        try:
            duracion_existente = minutos_de_duracion(func["duracion_minutos"])
        except (TypeError, ValueError):
            raise ValueError("La duración de una película existente no es válida.")

        if duracion_existente <= 0:
            raise ValueError("La duración de una película existente debe ser positiva.")
        fin_existente = inicio_existente + timedelta(minutes=duracion_existente)
        
        if inicio_nueva < fin_existente and fin_nueva > inicio_existente:
            return True # Hay choque de horarios
            
    return False # No hay solapamiento
