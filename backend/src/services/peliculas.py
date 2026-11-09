
import os
import re
from pathlib import Path
from backend.src.validators.duracion_validator import minutos_de_duracion
from flask import Flask, request, jsonify
import requests
import mysql.connector
from mysql.connector import Error
from deep_translator import MyMemoryTranslator
from dotenv import load_dotenv
app = Flask(__name__)
app.json.sort_keys = False
load_dotenv()




def descargar_poster(url_remota, titulo_pelicula):
    """Descarga la imagen desde la URL de OMDb y la guarda localmente"""
    if not url_remota or url_remota == 'N/A':
        return 'static/img/default.svg'

    try:

        nombre_limpio = re.sub(r'[^a-zA-Z0-9_\-]', '_', titulo_pelicula).lower()
        nombre_archivo = f"{nombre_limpio}.jpg"

        ruta_directorio = Path(__file__).resolve().parents[2] / "static" / "img"

        # Crear la carpeta si no existe
        os.makedirs(ruta_directorio, exist_ok=True)

        ruta_guardado = os.path.join(ruta_directorio, nombre_archivo)

        # Descargar los bytes de la imagen
        respuesta_imagen = requests.get(url_remota, stream=True, timeout=10)
        if respuesta_imagen.status_code == 200:
            with open(ruta_guardado, 'wb') as f:
                for chunk in respuesta_imagen.iter_content(1024):
                    f.write(chunk)
            return f"static/img/{nombre_archivo}"

    except Exception as e:
        print(f"Error al descargar el póster: {e}")

    return 'static/img/default.svg'

def pelicula_hallada (datos_omdb):
    traductor = MyMemoryTranslator(source='english', target='spanish')

    if datos_omdb.get ('Plot'):
        datos_omdb ['Plot'] = traductor.translate(datos_omdb['Plot'])

    if datos_omdb.get  ('Genre'):
        datos_omdb ['Genre'] = traductor.translate(datos_omdb['Genre'])

    resultado = {
                'titulo': datos_omdb.get('Title'),
                'sinopsis': datos_omdb.get('Plot'),
                'poster'  : datos_omdb.get('Poster'),
                'duracion_minutos': str(minutos_de_duracion(datos_omdb.get('Runtime'))),
                'clasificacion': datos_omdb.get('Rated'),
                'genero': datos_omdb.get('Genre')
             }
    return (resultado)

def pelicula_a_guardar (datos_omdb, url):
    traductor = MyMemoryTranslator(source='english', target='spanish')

    if datos_omdb.get ('Plot'):
        datos_omdb ['Plot'] = traductor.translate(datos_omdb['Plot'])

    if datos_omdb.get  ('Genre'):
        datos_omdb ['Genre'] = traductor.translate(datos_omdb['Genre'])

    resultado = {
                'id_externo_api': datos_omdb.get('imdbID'),
                'titulo': datos_omdb.get('Title'),
                'sinopsis': datos_omdb.get('Plot'),
                'poster'  : url,
                'duracion_minutos': str(minutos_de_duracion(datos_omdb.get('Runtime'))),
                'clasificacion': datos_omdb.get('Rated'),
                'genero': datos_omdb.get('Genre')
             }
    return resultado
