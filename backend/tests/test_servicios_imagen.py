import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("SECRET_KEY", "clave-de-prueba-servicios-mayor-a-32-caracteres")
from backend.app import app
from backend.src.routes import servicios_routes as rutas
from mysql.connector import IntegrityError


class ServiciosImagen(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        carpeta_anterior = app.static_folder
        app.static_folder = self.temporal.name
        self.addCleanup(setattr, app, "static_folder", carpeta_anterior)
        self.conexion = MagicMock()
        self.cursor = self.conexion.cursor.return_value.__enter__.return_value
        self.cursor.lastrowid = 12
        self.cursor.fetchone.return_value = {"id_servicio": 12, "imagen": "img/servicios/anterior.png"}
        self.datos = {"nombre": "Agua", "descripcion": "Botella de agua", "precio": "2000.00"}

    def escribir(self, identificador=None, **peticion):
        with app.test_request_context(**peticion), patch.object(rutas, "get_connection", return_value=self.conexion):
            return rutas.escribir_servicio(identificador)

    def archivos(self):
        return list(Path(self.temporal.name).rglob("*.*"))

    def test_json_anterior_sigue_funcionando_sin_imagen(self):
        _, estado = self.escribir(json=self.datos)
        self.assertEqual(estado, 201)
        parametros = self.cursor.execute.call_args.args[1]
        self.assertEqual(parametros[-1], "")
        self.conexion.commit.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_formulario_sin_imagen(self):
        _, estado = self.escribir(data=self.datos)
        self.assertEqual(estado, 201)
        self.assertFalse(self.archivos())

    def test_subida_guarda_nombre_unico_y_ruta(self):
        _, estado = self.escribir(data={**self.datos, "imagen": (BytesIO(b"imagen-prueba"), "../agua.png")})
        self.assertEqual(estado, 201)
        self.assertEqual(len(self.archivos()), 1)
        parametros = self.cursor.execute.call_args.args[1]
        self.assertTrue(parametros[-1].startswith("img/servicios/"))
        self.assertNotIn("..", parametros[-1])
        self.assertEqual(self.archivos()[0].read_bytes(), b"imagen-prueba")

    def test_edicion_sin_imagen_conserva_la_anterior(self):
        _, estado = self.escribir(12, data=self.datos)
        self.assertEqual(estado, 200)
        sql = self.cursor.execute.call_args.args[0]
        self.assertNotIn("imagen =", sql)

    def test_edicion_inexistente_no_deja_archivo(self):
        self.cursor.fetchone.return_value = None
        _, estado = self.escribir(99, data={**self.datos, "imagen": (BytesIO(b"imagen"), "agua.png")})
        self.assertEqual(estado, 404)
        self.assertFalse(self.archivos())
        self.conexion.commit.assert_not_called()

    def test_extension_invalida_no_abre_conexion(self):
        _, estado = self.escribir(data={**self.datos, "imagen": (BytesIO(b"script"), "agua.exe")})
        self.assertEqual(estado, 400)
        self.conexion.cursor.assert_not_called()
        self.assertFalse(self.archivos())

    def test_conflicto_sql_elimina_solo_imagen_nueva(self):
        self.cursor.execute.side_effect = IntegrityError("Nombre duplicado", errno=1062)
        _, estado = self.escribir(data={**self.datos, "imagen": (BytesIO(b"imagen"), "agua.png")})
        self.assertEqual(estado, 409)
        self.assertFalse(self.archivos())
        self.conexion.rollback.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_fallo_archivo_devuelve_error_controlado(self):
        with patch.object(rutas, "guardar_imagen", side_effect=OSError("Sin espacio")):
            _, estado = self.escribir(data={**self.datos, "imagen": (BytesIO(b"imagen"), "agua.png")})
        self.assertEqual(estado, 500)
        self.conexion.rollback.assert_called_once()
        self.conexion.commit.assert_not_called()
        self.conexion.close.assert_called_once()

    def test_datos_invalidos_se_rechazan_antes_de_escribir(self):
        for precio in (None, True, "NaN", "Infinity", "-1", "1.234", "100000000.00"):
            with self.subTest(precio=precio):
                _, estado = self.escribir(json={**self.datos, "precio": precio})
                self.assertEqual(estado, 400)
        self.conexion.cursor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
