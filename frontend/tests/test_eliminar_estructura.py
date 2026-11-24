import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SECRET_KEY", "clave-ficticia-para-pruebas-de-frontend-2026")
from frontend import app as frontend


class EliminarEstructura(unittest.TestCase):
    def setUp(self):
        frontend.app.config.update(TESTING=True)
        self.client = frontend.app.test_client()
        self.usuario = {"id_usuario": 8, "nombre": "Admin", "rol": "administrador"}
        self.respuesta = ({"mensaje": "Eliminación completada"}, 200)
        self.llamadas = []
        with self.client.session_transaction() as sesion:
            sesion["backend_token"] = "token-de-prueba"
            sesion["csrf_token"] = "csrf-de-prueba"
        parche = patch.object(frontend, "llamar_backend", side_effect=self.backend)
        parche.start()
        self.addCleanup(parche.stop)

    def backend(self, metodo, ruta, **argumentos):
        self.llamadas.append((metodo, ruta))
        if ruta == "/usuarios/me":
            return self.usuario, 200
        if metodo == "DELETE":
            return self.respuesta
        if ruta == "/locales":
            return {"locales": [{"id_local": 7, "nombre": "Local", "direccion": "Calle 123"}]}, 200
        return {"salas": [{"id_sala": 7, "nombre": "Sala", "capacidad": 50}]}, 200

    def test_botones_tienen_confirmacion_y_csrf(self):
        for recurso, etiqueta in (("locales", b"Eliminar local"), ("salas", b"Eliminar sala")):
            respuesta = self.client.get(f"/admin/{recurso}")
            self.assertEqual(respuesta.status_code, 200)
            self.assertIn(etiqueta, respuesta.data)
            self.assertIn(f'/admin/{recurso}/7/eliminar'.encode(), respuesta.data)
            self.assertIn(b"return confirm(", respuesta.data)
            self.assertIn(b'name="csrf_token"', respuesta.data)

    def test_eliminar_usa_delete_y_muestra_confirmacion(self):
        for recurso in ("locales", "salas"):
            respuesta = self.client.post(f"/admin/{recurso}/7/eliminar", data={"csrf_token": "csrf-de-prueba"}, follow_redirects=True)
            self.assertEqual(respuesta.status_code, 200)
            self.assertIn(("DELETE", f"/{recurso}/7"), self.llamadas)
            self.assertIn(b"Eliminaci", respuesta.data)

    def test_conflicto_es_visible(self):
        self.respuesta = ({"error": "Hay funciones asociadas"}, 409)
        for recurso in ("locales", "salas"):
            respuesta = self.client.post(f"/admin/{recurso}/7/eliminar", data={"csrf_token": "csrf-de-prueba"}, follow_redirects=True)
            self.assertIn(b"Hay funciones asociadas", respuesta.data)

    def test_sin_csrf_o_cliente_no_envia_delete(self):
        for recurso in ("locales", "salas"):
            self.assertEqual(self.client.post(f"/admin/{recurso}/7/eliminar").status_code, 400)
        self.usuario["rol"] = "cliente"
        for recurso in ("locales", "salas"):
            self.assertEqual(self.client.post(f"/admin/{recurso}/7/eliminar", data={"csrf_token": "csrf-de-prueba"}).status_code, 403)
        self.assertFalse(any(metodo == "DELETE" for metodo, _ in self.llamadas))

    def test_no_se_puede_borrar_con_get(self):
        for recurso in ("locales", "salas"):
            self.assertEqual(self.client.get(f"/admin/{recurso}/7/eliminar").status_code, 405)
        self.assertFalse(any(metodo == "DELETE" for metodo, _ in self.llamadas))
