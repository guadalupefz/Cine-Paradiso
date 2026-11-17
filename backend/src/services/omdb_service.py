import os
import re
from pathlib import Path

import requests
from deep_translator import MyMemoryTranslator

from backend.src.repositories.peliculas import guardar_pelicula
from backend.src.validators.duracion_validator import minutos_de_duracion


OMDB_URL = "https://www.omdbapi.com/"
TIMEOUT = 10
POSTER_FALTANTE = "static/img/poster_sin_imagen.svg"


class OMDbError(Exception):
    pass


def _obtener_api_key():
    api_key = os.getenv("OMDB_API_KEY")
    if not api_key:
        raise OMDbError("La API externa no está configurada.")
    return api_key


def consultar_omdb(parametros):
    try:
        parametros = parametros.copy()
        parametros["apikey"] = _obtener_api_key()
        respuesta = requests.get(
            os.getenv("OMDB_URL", OMDB_URL),
            params=parametros,
            timeout=TIMEOUT,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()
    except OMDbError as error:
        return None, {"error": str(error)}, 503
    except requests.exceptions.Timeout:
        return None, {"error": "OMDb tardó demasiado en responder."}, 504
    except requests.exceptions.ConnectionError:
        return None, {"error": "No se pudo establecer conexión con OMDb."}, 502
    except requests.exceptions.HTTPError:
        return None, {"error": "OMDb devolvió un error HTTP."}, 502
    except requests.exceptions.RequestException:
        return None, {"error": "Error de comunicación con OMDb."}, 502
    except ValueError:
        return None, {"error": "OMDb devolvió una respuesta inválida."}, 502

    if datos.get("Response") == "False":
        return None, {
            "error": datos.get("Error", "No se encontraron resultados.")
        }, 404
    return datos, None, 200


def traducir_texto(texto):
    if not texto or texto == "N/A":
        return texto
    try:
        return MyMemoryTranslator(
            source="english",
            target="spanish",
        ).translate(texto)
    except Exception:
        return texto


def pelicula_hallada(datos_omdb):
    poster = datos_omdb.get("Poster")
    return {
        "id_externo_api": datos_omdb.get("imdbID"),
        "titulo": datos_omdb.get("Title"),
        "sinopsis": traducir_texto(datos_omdb.get("Plot")),
        "poster": poster if poster and poster != "N/A" else None,
        "duracion_minutos": minutos_de_duracion(datos_omdb.get("Runtime")),
        "clasificacion": datos_omdb.get("Rated"),
        "genero": traducir_texto(datos_omdb.get("Genre")),
    }


def descargar_poster(url_remota, titulo_pelicula):
    if not url_remota or url_remota == "N/A":
        return POSTER_FALTANTE
    try:
        nombre = re.sub(r"[^a-zA-Z0-9_-]", "_", titulo_pelicula or "pelicula").lower()
        ruta_directorio = Path(__file__).resolve().parents[2] / "static" / "img"
        ruta_directorio.mkdir(parents=True, exist_ok=True)
        ruta_guardado = ruta_directorio / f"{nombre}.jpg"
        respuesta = requests.get(url_remota, stream=True, timeout=TIMEOUT)
        respuesta.raise_for_status()
        with open(ruta_guardado, "wb") as archivo:
            for fragmento in respuesta.iter_content(1024):
                if fragmento:
                    archivo.write(fragmento)
        return f"static/img/{ruta_guardado.name}"
    except (requests.exceptions.RequestException, OSError):
        return "static/img/default.svg"


def buscar_peliculas_omdb_service(titulo):
    datos, error, estado = consultar_omdb({
        "s": titulo,
        "type": "movie",
    })
    if error:
        return {"data": error, "status": estado}
    peliculas = [
        {
            "id_externo_api": item.get("imdbID"),
            "titulo": item.get("Title"),
            "anio": item.get("Year"),
            "poster": item.get("Poster") if item.get("Poster") != "N/A" else None,
        }
        for item in datos.get("Search", [])
    ]
    return {"data": {"peliculas": peliculas}, "status": 200}


def obtener_detalle_omdb_service(imdb_id):
    datos, error, estado = consultar_omdb({
        "i": imdb_id,
        "plot": "full",
    })
    if error:
        return {"data": error, "status": estado}
    try:
        return {"data": pelicula_hallada(datos), "status": 200}
    except (ValueError, TypeError):
        return {
            "data": {"error": "No se pudieron procesar los datos de OMDb."},
            "status": 422,
        }


def importar_pelicula_omdb_service(imdb_id, id_usuario=None):
    datos, error, estado = consultar_omdb({
        "i": imdb_id,
        "plot": "full",
    })
    if error:
        return {"data": error, "status": estado}
    try:
        pelicula = pelicula_hallada(datos)
        pelicula["poster"] = descargar_poster(
            datos.get("Poster"),
            pelicula["titulo"],
        )
        resultado = guardar_pelicula(pelicula)
        if not resultado["exito"]:
            return {"data": {"error": resultado["error"]}, "status": 500}
        return {
            "data": {
                "mensaje": "Película importada correctamente.",
                "id_externo_api": pelicula["id_externo_api"],
                "titulo": pelicula["titulo"],
                "accion": resultado["accion"],
            },
            "status": 201,
        }
    except (ValueError, TypeError):
        return {
            "data": {"error": "No se pudieron procesar los datos de la película."},
            "status": 422,
        }


def buscar_pelicula_por_titulo(titulo):
    datos, error, estado = consultar_omdb({
        "t": titulo,
        "type": "movie",
        "plot": "full",
    })
    if error:
        return error, estado
    try:
        return pelicula_hallada(datos), 200
    except (ValueError, TypeError):
        return {"error": "No se pudieron procesar los datos de OMDb."}, 422


def importar_pelicula_por_titulo(titulo):
    datos, error, estado = consultar_omdb({
        "t": titulo,
        "type": "movie",
        "plot": "full",
    })
    if error:
        return error, estado
    try:
        pelicula = pelicula_hallada(datos)
        pelicula["poster"] = descargar_poster(
            datos.get("Poster"),
            pelicula["titulo"],
        )
        resultado = guardar_pelicula(pelicula)
        if not resultado["exito"]:
            return {"error": resultado["error"]}, 500
        if resultado["accion"] == "actualizada":
            return {" Error": "La película ya se encuentra cargada"}, 200
        return pelicula, 201
    except (ValueError, TypeError):
        return {"error": "No se pudieron procesar los datos de la película."}, 422
