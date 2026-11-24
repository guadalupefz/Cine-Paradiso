import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("SECRET_KEY", "clave-ficticia")

from backend.src.repositories import peliculas_repository as repo
from backend.src.services import omdb_service


class RespuestaOMDb:
    def __init__(self, datos):
        self.datos = datos

    def raise_for_status(self):
        return None

    def json(self):
        return self.datos


class ConexionOMDbFicticia:
    def __init__(self):
        self.filas = {}
        self.siguiente_id = 1

    def cursor(self, **kwargs):
        return CursorOMDbFicticio(self)


class CursorOMDbFicticio:
    def __init__(self, conexion):
        self.conexion = conexion
        self.lastrowid = None

    def execute(self, query, valores=None):
        query_normalizada = " ".join(query.split())
        valores = valores or ()

        if query_normalizada.startswith(
            "SELECT id_pelicula FROM pelicula WHERE id_externo_api"
        ):
            fila = self.conexion.filas.get(valores[0])
            self._fila = {"id_pelicula": fila["id_pelicula"]} if fila else None
            return

        if query_normalizada.startswith("UPDATE pelicula SET"):
            id_externo_api = valores[-1]
            fila = self.conexion.filas[id_externo_api]
            fila.update({
                "titulo": valores[0],
                "sinopsis": valores[1],
                "poster": valores[2],
                "duracion_minutos": valores[3],
                "clasificacion": valores[4],
                "genero": valores[5],
            })
            return

        if query_normalizada.startswith("INSERT INTO pelicula"):
            id_externo_api = valores[0]
            id_pelicula = self.conexion.siguiente_id
            self.conexion.siguiente_id += 1
            self.conexion.filas[id_externo_api] = {
                "id_pelicula": id_pelicula,
                "id_externo_api": id_externo_api,
                "titulo": valores[1],
                "sinopsis": valores[2],
                "poster": valores[3],
                "duracion_minutos": valores[4],
                "clasificacion": valores[5],
                "genero": valores[6],
            }
            self.lastrowid = id_pelicula

    def fetchone(self):
        return getattr(self, "_fila", None)


class ImportacionOMDbTest(unittest.TestCase):
    def datos_locales(self, titulo, sinopsis):
        return {
            "id_externo_api": "tt0068646",
            "titulo": titulo,
            "sinopsis": sinopsis,
            "poster": "poster.jpg",
            "duracion_minutos": 175,
            "clasificacion": "R",
            "genero": "Crime, Drama",
        }

    def test_busqueda_normaliza_resultados(self):
        with patch.dict(os.environ, {"OMDB_API_KEY": "clave-ficticia"}), patch.object(
            omdb_service.requests,
            "get",
            return_value=RespuestaOMDb({
                "Response": "True",
                "Search": [{
                    "imdbID": "tt0133093",
                    "Title": "The Matrix",
                    "Year": "1999",
                    "Poster": "N/A",
                }],
                "totalResults": "1",
            }),
        ):
            resultado = omdb_service.buscar_peliculas("Matrix")

        self.assertEqual(resultado["pagina"], 1)
        self.assertEqual(resultado["peliculas"][0]["id_imdb"], "tt0133093")
        self.assertIsNone(resultado["peliculas"][0]["poster"])

    def test_detalle_normaliza_pelicula(self):
        with patch.dict(os.environ, {"OMDB_API_KEY": "clave-ficticia"}), patch.object(
            omdb_service.requests,
            "get",
            return_value=RespuestaOMDb({
                "Response": "True",
                "imdbID": "tt0068646",
                "Title": "The Godfather",
                "Year": "1972",
                "Genre": "Crime, Drama",
                "Plot": "A crime drama.",
                "Runtime": "175 min",
                "Rated": "R",
                "Poster": "poster.jpg",
            }),
        ):
            pelicula = omdb_service.obtener_pelicula_por_id("tt0068646")

        self.assertEqual(pelicula["id_imdb"], "tt0068646")
        self.assertEqual(pelicula["clasificacion"], "R")
        self.assertEqual(
            omdb_service.preparar_pelicula_para_guardar(pelicula),
            self.datos_locales("The Godfather", "A crime drama."),
        )

    def test_error_de_omdb_se_propaga_como_valor_invalido(self):
        with patch.dict(os.environ, {"OMDB_API_KEY": "clave-ficticia"}), patch.object(
            omdb_service.requests,
            "get",
            return_value=RespuestaOMDb({
                "Response": "False",
                "Error": "Movie not found!",
            }),
        ), self.assertRaisesRegex(ValueError, "Movie not found"):
            omdb_service.obtener_pelicula_por_id("tt9999999")

    def test_sin_api_key_devuelve_error_explicito(self):
        with patch.dict(os.environ, {"OMDB_API_KEY": ""}), self.assertRaisesRegex(
            ValueError, "API Key"
        ):
            omdb_service.buscar_peliculas("Matrix")

    def test_timeout_se_propaga_como_timeout_error(self):
        with patch.dict(os.environ, {"OMDB_API_KEY": "clave-ficticia"}), patch.object(
            omdb_service.requests,
            "get",
            side_effect=omdb_service.requests.exceptions.Timeout(),
        ), self.assertRaises(TimeoutError):
            omdb_service.buscar_peliculas("Matrix")

    def test_importar_actualiza_un_registro_por_imdb_id(self):
        conexion = ConexionOMDbFicticia()
        primera = repo.guardar_pelicula(
            conexion.cursor(dictionary=True),
            self.datos_locales("The Godfather", "Aging patriarch."),
        )
        segunda = repo.guardar_pelicula(
            conexion.cursor(dictionary=True),
            self.datos_locales("El padrino", "Drama actualizado."),
        )

        self.assertEqual(primera["accion"], "insertada")
        self.assertEqual(segunda["accion"], "actualizada")
        self.assertEqual(len(conexion.filas), 1)
        self.assertEqual(
            conexion.filas["tt0068646"]["sinopsis"],
            "Drama actualizado.",
        )

    def test_imdb_id_faltante_no_intenta_insertar(self):
        conexion = ConexionOMDbFicticia()
        datos = self.datos_locales("The Godfather", "Sinopsis")
        datos["id_externo_api"] = None

        resultado = repo.guardar_pelicula(
            conexion.cursor(dictionary=True),
            datos,
        )

        self.assertFalse(resultado["exito"])
        self.assertEqual(resultado["error"], "OMDb no devolvió imdbID")
        self.assertEqual(len(conexion.filas), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
