import os
import requests

from backend.src.validators.duracion_validator import minutos_de_duracion

OMDB_URL = "https://www.omdbapi.com/"
TIMEOUT = 10

def _obtener_api_key():
    api_key = os.getenv("OMDB_API_KEY")

    if not api_key:
        raise ValueError("No está configurada la API Key de OMDb.")

    return api_key

def _consultar_omdb(parametros):
    parametros["apikey"] = _obtener_api_key()

    try:
        respuesta = requests.get(
            OMDB_URL,
            params=parametros,
            timeout=TIMEOUT
        )

        respuesta.raise_for_status()
        datos = respuesta.json()

    except requests.exceptions.Timeout:
        raise TimeoutError("La API de OMDb tardó demasiado en responder.")

    except requests.exceptions.ConnectionError:
        raise ConnectionError("No se pudo establecer conexión con OMDb.")

    except requests.exceptions.HTTPError:
        raise RuntimeError("OMDb devolvió un error HTTP.")

    except requests.exceptions.RequestException:
        raise RuntimeError("Ocurrió un error al consultar OMDb.")

    except ValueError:
        raise ValueError("OMDb devolvió una respuesta JSON inválida.")

    if datos.get("Response") == "False":
        raise ValueError(
            datos.get("Error", "No se encontraron resultados.")
        )

    return datos

def _normalizar_pelicula(datos):
    poster = datos.get("Poster")

    return {
        "id_imdb": datos.get("imdbID"),
        "titulo": datos.get("Title"),
        "anio": datos.get("Year"),
        "genero": datos.get("Genre"),
        "sinopsis": datos.get("Plot"),
        "duracion": datos.get("Runtime"),
        "director": datos.get("Director"),
        "reparto": datos.get("Actors"),
        "calificacion_imdb": datos.get("imdbRating"),
        "clasificacion": datos.get("Rated"),
        "poster": poster if poster != "N/A" else None
    }


def preparar_pelicula_para_guardar(pelicula):
    id_imdb = pelicula.get("id_imdb")
    if not isinstance(id_imdb, str) or not id_imdb:
        raise ValueError("OMDb no devolvió un identificador IMDb válido.")

    return {
        "id_externo_api": id_imdb,
        "titulo": pelicula["titulo"],
        "sinopsis": pelicula["sinopsis"],
        "poster": pelicula["poster"],
        "duracion_minutos": minutos_de_duracion(pelicula["duracion"]),
        "clasificacion": pelicula["clasificacion"],
        "genero": pelicula["genero"],
    }

def buscar_peliculas(titulo, pagina=1):
    if not titulo or not titulo.strip():
        raise ValueError("Debés ingresar un título para buscar.")

    if not isinstance(pagina, int) or not 1 <= pagina <= 100:
        raise ValueError("La página debe ser un número entre 1 y 100.")

    datos = _consultar_omdb({
        "s": titulo.strip(),
        "type": "movie",
        "page": pagina
    })

    peliculas = [
        {
            "id_imdb": pelicula.get("imdbID"),
            "titulo": pelicula.get("Title"),
            "anio": pelicula.get("Year"),
            "poster": (
                pelicula.get("Poster")
                if pelicula.get("Poster") != "N/A"
                else None
            )
        }
        for pelicula in datos.get("Search", [])
    ]

    return {
        "total_resultados": int(datos.get("totalResults", 0)),
        "pagina": pagina,
        "peliculas": peliculas
    }

def obtener_pelicula_por_id(id_imdb):
    if not id_imdb or not id_imdb.strip():
        raise ValueError("Debés proporcionar un identificador IMDb.")

    datos = _consultar_omdb({
        "i": id_imdb.strip(),
        "plot": "full"
    })

    return _normalizar_pelicula(datos)

def obtener_pelicula_por_titulo(titulo):
    if not titulo or not titulo.strip():
        raise ValueError("Debés proporcionar un título.")

    datos = _consultar_omdb({
        "t": titulo.strip(),
        "type": "movie",
        "plot": "full"
    })

    return _normalizar_pelicula(datos)
