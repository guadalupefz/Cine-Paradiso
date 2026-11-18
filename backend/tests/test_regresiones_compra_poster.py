import sqlite3
import unittest

from backend.src.repositories.compra_repository import actualizar_qr_entrada
from backend.src.services.omdb_service import preparar_pelicula_para_guardar
from backend.src.validators.peliculas_validator import validar_pelicula


class CursorCompatible:
    def __init__(self, conexion):
        self.conexion = conexion

    def execute(self, consulta, parametros):
        self.conexion.execute(consulta.replace("%s", "?"), parametros)


class RegresionesCompraPoster(unittest.TestCase):
    def test_confirmacion_cambia_solo_el_qr_de_la_entrada_indicada(self):
        with sqlite3.connect(":memory:") as conexion:
            conexion.execute(
                "CREATE TABLE entrada (id_entrada INTEGER PRIMARY KEY, qr_token TEXT UNIQUE)"
            )
            conexion.executemany(
                "INSERT INTO entrada VALUES (?, ?)",
                [(19, "reserva-19"), (20, "reserva-20")],
            )

            actualizar_qr_entrada(CursorCompatible(conexion), 19, "entrada-confirmada")

            filas = conexion.execute(
                "SELECT id_entrada, qr_token FROM entrada ORDER BY id_entrada"
            ).fetchall()
            self.assertEqual(
                filas, [(19, "entrada-confirmada"), (20, "reserva-20")]
            )

    def datos_pelicula(self):
        return {
            "titulo": "Película de prueba",
            "sinopsis": "Sinopsis",
            "poster": "https://example.com/" + "a" * 150 + ".jpg",
            "clasificacion": "+13",
            "genero": "Drama",
            "duracion_minutos": 90,
        }

    def test_url_de_poster_larga_cabe_en_el_contrato(self):
        datos = self.datos_pelicula()
        pelicula, error = validar_pelicula(datos)
        self.assertIsNone(error)
        self.assertEqual(pelicula["poster"], datos["poster"])

    def test_url_fuera_del_limite_se_rechaza_antes_de_mysql(self):
        datos = self.datos_pelicula()
        datos["poster"] = "https://example.com/" + "a" * 2048
        pelicula, error = validar_pelicula(datos)
        self.assertIsNone(pelicula)
        self.assertIn("poster", error)

    def test_importacion_sin_poster_utiliza_imagen_predeterminada(self):
        datos = {
            "id_imdb": "tt1234567",
            "titulo": "Película de prueba",
            "sinopsis": "Sinopsis",
            "poster": None,
            "duracion": "90 min",
            "clasificacion": "+13",
            "genero": "Drama",
        }
        pelicula = preparar_pelicula_para_guardar(datos)
        self.assertEqual(pelicula["poster"], "/static/img/default.svg")


if __name__ == "__main__":
    unittest.main()
