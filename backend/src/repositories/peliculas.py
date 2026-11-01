from db import ejecutar_buscar, ejecutar_guardar


def buscar_pelicula (titulo):

    
    
    query = "SELECT titulo FROM pelicula WHERE titulo = %s"
     
    film_procurado = ejecutar_buscar(query, (titulo,))
    if film_procurado["exito"] and film_procurado["datos"]:
       return True
    return False

def guardar_pelicula (datos):
     
    query = """
                INSERT INTO pelicula (titulo, sinopsis, poster, duracion_minutos, clasificacion, genero)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
    valores = (
                datos['titulo'],
                datos['sinopsis'],
                datos['poster'],
                datos['duracion_minutos'],
                datos['clasificacion'],
                datos['genero']
            )
            
    film_guardado = ejecutar_guardar(query, valores)

    if film_guardado ["exito"]:
        return True
    return False

  
            
    

