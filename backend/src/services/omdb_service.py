import os
import requests

OMDB_URL = "https://www.omdbapi.com/"
TIMEOUT = 10


class OMDbError(Exception):
    """Error producido durante una consulta a OMDb."""
    pass


def _obtener_api_key():
    api_key = os.getenv("OMDB_API_KEY")

    if not api_key:
        raise OMDbError("No está configurada la API Key de OMDb.")

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
        raise OMDbError("La API de OMDb tardó demasiado en responder.")

    except requests.exceptions.ConnectionError:
        raise OMDbError("No se pudo establecer conexión con OMDb.")

    except requests.exceptions.HTTPError:
        raise OMDbError("OMDb devolvió un error HTTP.")

    except requests.exceptions.RequestException:
        raise OMDbError("Ocurrió un error al consultar OMDb.")

    except ValueError:
        raise OMDbError("OMDb devolvió una respuesta inválida.")

    if datos.get("Response") == "False":
        raise OMDbError(
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
        "poster": poster if poster != "N/A" else None
    }


def buscar_peliculas(titulo, pagina=1):
    if not titulo or not titulo.strip():
        raise OMDbError("Debés ingresar un título para buscar.")

    if not isinstance(pagina, int) or not 1 <= pagina <= 100:
        raise OMDbError("La página debe ser un número entre 1 y 100.")

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
        raise OMDbError("Debés proporcionar un identificador IMDb.")

    datos = _consultar_omdb({
        "i": id_imdb.strip(),
        "plot": "full"
    })

    return _normalizar_pelicula(datos)


def obtener_pelicula_por_titulo(titulo):
    if not titulo or not titulo.strip():
        raise OMDbError("Debés proporcionar un título.")

    datos = _consultar_omdb({
        "t": titulo.strip(),
        "type": "movie",
        "plot": "full"
    })

    return _normalizar_pelicula(datos)
