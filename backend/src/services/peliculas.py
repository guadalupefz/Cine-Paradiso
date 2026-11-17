import os
import re
from pathlib import Path
import requests
from deep_translator import MyMemoryTranslator
from backend.src.validators.duracion_validator import (
    minutos_de_duracion
)
from backend.src.repositories.peliculas import (
    sincronizar_pelicula
)

OMDB_API_KEY = os.getenv("373df741")
OMDB_URL = os.getenv(
    "OMDB_URL",
    "https://www.omdbapi.com/"
)

def consultar_omdb(parametros):
    if not OMDB_API_KEY:
        return None, {
            "error": "La API de OMDb no está configurada."
        }, 503

    parametros = parametros.copy()
    parametros["apikey"] = OMDB_API_KEY

    try:
        respuesta = requests.get(
            OMDB_URL,
            params=parametros,
            timeout=10
        )
        respuesta.raise_for_status()
        datos = respuesta.json()

        if datos.get("Response") == "False":
            return None, {
                "error": datos.get("Error", "Película no encontrada.")
            }, 404

        return datos, None, 200
    except requests.exceptions.Timeout:
        return None, {
            "error": "OMDb tardó demasiado en responder."
        }, 504

    except requests.exceptions.RequestException:
        return None, {
            "error": "Error de comunicación con OMDb."
        }, 502

    except ValueError:
        return None, {
            "error": "OMDb devolvió una respuesta inválida."
        }, 502

def traducir_texto(texto):
    """esta poronga traduce texto de ingles a español para la api externa que muestra en ignles"""
    if not texto or texto == "N/A":
        return texto

    try:
        traductor = MyMemoryTranslator(
            source="english",
            target="spanish"
        )
        return traductor.translate(texto)

    except Exception:
        return texto


def pelicula_hallada(datos_omdb):
    return {
        "id_externo_api": datos_omdb.get("imdbID"),
        "titulo": datos_omdb.get("Title"),
        "sinopsis": traducir_texto(datos_omdb.get("Plot")),
        "poster": datos_omdb.get("Poster"),
        "duracion_minutos": minutos_de_duracion(
            datos_omdb.get("Runtime")
        ),
        "clasificacion": datos_omdb.get("Rated"),
        "genero": traducir_texto(datos_omdb.get("Genre"))
    }


def pelicula_a_guardar(datos_omdb, url_poster):
    pelicula = pelicula_hallada(datos_omdb)
    pelicula["poster"] = url_poster

    return pelicula

def descargar_poster(url_remota, titulo_pelicula):
    """descarga el poster y lo guarda localmente"""
    if not url_remota or url_remota == "N/A":
        return "static/img/poster_de_la_pei.svg"

    try:
        nombre_limpio = re.sub(
            r"[^a-zA-Z0-9_-]",
            "_",
            titulo_pelicula
        ).lower()
        
        nombre_archivo = f"{nombre_limpio}.jpg"
        ruta_directorio = (
            Path(__file__).resolve().parents[2]
            / "static"
            / "img"
        )

        ruta_directorio.mkdir(
            parents=True,
            exist_ok=True
        )

        ruta_guardado = ruta_directorio / nombre_archivo

        respuesta = requests.get(
            url_remota,
            stream=True,
            timeout=10
        )

        respuesta.raise_for_status()
        with open(ruta_guardado, "wb") as archivo:
            for fragmento in respuesta.iter_content(1024):
                if fragmento:
                    archivo.write(fragmento)

        return f"static/img/{nombre_archivo}"

    except (requests.exceptions.RequestException, OSError):
        return "static/img/default.svg"

def buscar_peliculas_omdb_service(titulo):
    datos, error, estado = consultar_omdb({
        "s": titulo,
        "type": "movie"
    })

    if error:
        return {
            "data": error,
            "status": estado
        }
    
    peliculas = []

    for pelicula in datos.get("Search", []):
        peliculas.append({
            "id_externo_api": pelicula.get("imdbID"),
            "titulo": pelicula.get("Title"),
            "anio": pelicula.get("Year"),
            "poster": pelicula.get("Poster")
        })

    return {
        "data": {"peliculas": peliculas},
        "status": 200
    }

def obtener_detalle_omdb_service(imdb_id):
    datos, error, estado = consultar_omdb({
        "i": imdb_id,
        "plot": "full"
    })

    if error:
        return {
            "data": error,
            "status": estado
        }

    try:
        pelicula = pelicula_hallada(datos)
        return {
            "data": pelicula,
            "status": 200
        }

    except (ValueError, TypeError):
        return {
            "data": {
                "error": "No se pudieron procesar los datos de OMDb."
            },
            "status": 422
        }

def importar_pelicula_omdb_service(cursor, imdb_id):
    """
    obtiene una película de omdb y la prepara
    para sincronizarla con el catalogo local

    el cursor pertenece a la conexión administrada
    por la capa Repository o por quien haga la transacción
    """

    datos, error, estado = consultar_omdb({
        "i": imdb_id,
        "plot": "full"
    })

    if error:
        return {
            "data": error,
            "status": estado
        }

    try:
        pelicula = pelicula_hallada(datos)
        pelicula["poster"] = descargar_poster(datos.get("Poster"), pelicula["titulo"])
        sincronizar_pelicula(cursor, pelicula)

        return {
            "data": {
                "mensaje": "Película importada correctamente.",
                "id_externo_api": pelicula["id_externo_api"],
                "titulo": pelicula["titulo"]
            },
            "status": 201
        }

    except (ValueError, TypeError):
        return {
            "data": {
                "error": "No se pudieron procesar los datos de la película."
            },
            "status": 422
        }
