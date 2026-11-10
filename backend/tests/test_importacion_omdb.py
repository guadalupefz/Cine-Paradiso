import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("SECRET_KEY", "clave-ficticia")

from backend.src.repositories import peliculas as repo


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
        self.commit_count = 0
        self.rollback_count = 0
        self.cerrada = False

    def cursor(self, **kwargs):
        return CursorOMDbFicticio(self)

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def close(self):
        self.cerrada = True


class CursorOMDbFicticio:
    def __init__(self, conexion):
        self.conexion = conexion
        self.lastrowid = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, valores=None):
        query_normalizada = " ".join(query.split())
        valores = valores or ()

        if query_normalizada.startswith("SELECT id_pelicula FROM pelicula WHERE id_externo_api"):
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
    def datos_api(self, titulo, sinopsis):
        return {
            "Response": "True",
            "imdbID": "tt0068646",
            "Title": titulo,
            "Plot": sinopsis,
            "Poster": "static/img/godfather.jpg",
            "Runtime": "175 min",
            "Rated": "R",
            "Genre": "Crime, Drama",
        }

    def datos_local(self, datos):
        return {
            "id_externo_api": datos["imdbID"],
            "titulo": datos["Title"],
            "sinopsis": datos["Plot"],
            "poster": datos["Poster"],
            "duracion_minutos": 175,
            "clasificacion": datos["Rated"],
            "genero": datos["Genre"],
        }

    def test_misma_pelicula_en_dos_busquedas_actualiza_un_registro(self):
        conexion = ConexionOMDbFicticia()

        with patch.object(repo, "get_connection", return_value=conexion):
            primera = repo.guardar_pelicula(
                self.datos_local(self.datos_api("The Godfather", "The aging patriarch"))
            )
            segunda = repo.guardar_pelicula(
                self.datos_local(self.datos_api("El padrino", "Drama de mafia actualizado"))
            )

        self.assertTrue(primera["exito"])
        self.assertEqual(primera["accion"], "insertada")
        self.assertTrue(segunda["exito"])
        self.assertEqual(segunda["accion"], "actualizada")
        self.assertEqual(len(conexion.filas), 1)
        guardada = conexion.filas["tt0068646"]
        self.assertEqual(guardada["id_pelicula"], primera["id"])
        self.assertEqual(guardada["titulo"], "El padrino")
        self.assertEqual(guardada["sinopsis"], "Drama de mafia actualizado")
        self.assertEqual(conexion.commit_count, 2)
        self.assertTrue(conexion.cerrada)

    def test_imdb_id_faltante_no_intenta_insertar(self):
        conexion = ConexionOMDbFicticia()
        datos = self.datos_local(self.datos_api("The Godfather", "Sinopsis"))
        datos["id_externo_api"] = None

        with patch.object(repo, "get_connection", return_value=conexion):
            resultado = repo.guardar_pelicula(datos)

        self.assertFalse(resultado["exito"])
        self.assertEqual(resultado["error"], "OMDb no devolvió imdbID")
        self.assertEqual(len(conexion.filas), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
