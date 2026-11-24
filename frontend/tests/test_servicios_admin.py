import os
from io import BytesIO
import unittest
from urllib.parse import urlsplit, parse_qs
from unittest.mock import patch

os.environ.setdefault("SECRET_KEY", "clave-ficticia-para-pruebas-de-frontend-2026")
from frontend import app as frontend
from backend.src.routes.servicios_routes import validar_servicio


class ServiciosAdmin(unittest.TestCase):
    def setUp(self):
        frontend.app.config.update(TESTING=True)
        self.client = frontend.app.test_client()
        self.usuario = {"id_usuario": 8, "nombre": "Admin", "rol": "administrador"}
        self.servicios = [{"id_servicio": 7, "nombre": "Pochoclos", "descripcion": "Balde grande", "precio": "6000.00"}]
        self.listado = (self.servicios, 200)
        self.escritura = ({"mensaje": "Servicio guardado", "id_servicio": 7}, 201)
        self.llamadas = []
        with self.client.session_transaction() as sesion:
            sesion["backend_token"] = "token-de-prueba"
            sesion["csrf_token"] = "csrf-de-prueba"
        parche = patch.object(frontend, "llamar_backend", side_effect=self.backend)
        parche.start()
        self.addCleanup(parche.stop)

    def backend(self, metodo, ruta, **argumentos):
        self.llamadas.append((metodo, ruta, argumentos))
        if ruta == "/usuarios/me":
            return self.usuario, 200
        if metodo == "GET" and ruta == "/servicios":
            return self.listado
        if metodo in ("POST", "PUT") and ruta.startswith("/servicios"):
            try:
                validar_servicio(argumentos.get("data"))
            except ValueError as error:
                return {"error": str(error)}, 400
        return self.escritura

    def post(self, **datos):
        return self.client.post("/admin/servicios", data={"csrf_token": "csrf-de-prueba", "descripcion": "Descripción de prueba", **datos})

    def test_listado_y_edicion(self):
        respuesta = self.client.get("/admin/servicios?editar=7")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b'value="Pochoclos"', respuesta.data)
        self.assertIn(b'value="6000.00"', respuesta.data)
        self.assertIn(b'name="id_servicio" value="7"', respuesta.data)
        self.assertIn(b"Balde grande</textarea>", respuesta.data)

    def test_crear_envia_datos_y_redirige(self):
        respuesta = self.post(accion="crear", nombre="Agua", precio="2000.00")
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.location, "/admin/servicios")
        self.assertIn(("POST", "/servicios", {"data": {"nombre": "Agua", "descripcion": "Descripción de prueba", "precio": "2000.00"}}), self.llamadas)

    def test_editar_envia_id_y_datos(self):
        self.escritura = ({"mensaje": "Servicio guardado"}, 200)
        respuesta = self.post(accion="editar", id_servicio="7", nombre="Balde", precio="6500.00")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(("PUT", "/servicios/7", {"data": {"nombre": "Balde", "descripcion": "Descripción de prueba", "precio": "6500.00"}}), self.llamadas)

    def test_imagen_se_envia_junto_con_descripcion(self):
        respuesta = self.post(accion="crear", nombre="Agua", precio="2000.00",
                              imagen=(BytesIO(b"contenido-imagen"), "agua.png"))
        self.assertEqual(respuesta.status_code, 302)
        enviados = next(args for metodo, ruta, args in self.llamadas if metodo == "POST")
        self.assertEqual(enviados["data"]["descripcion"], "Descripción de prueba")
        self.assertEqual(enviados["files"]["imagen"][0], "agua.png")

    def test_miniatura_apunta_al_backend(self):
        self.servicios[0]["imagen"] = "img/servicios/agua.png"
        respuesta = self.client.get("/admin/servicios")
        self.assertIn((frontend.BACKEND_ORIGEN + "/static/img/servicios/agua.png").encode(), respuesta.data)

    def test_imagen_de_dos_megabytes_llega_al_backend(self):
        contenido = b"x" * (2 * 1024 * 1024)
        imagenes = []
        def capturar(metodo, ruta, **argumentos):
            if argumentos.get("files"):
                imagenes.append(argumentos["files"]["imagen"][1].read())
            return self.backend(metodo, ruta, **argumentos)
        with patch.object(frontend, "llamar_backend", side_effect=capturar):
            respuesta = self.post(accion="crear", nombre="Combo", precio="6000.00",
                                  imagen=(BytesIO(contenido), "combo.png"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(imagenes, [contenido])

    def test_imagen_excesiva_muestra_mensaje_y_no_envia_escritura(self):
        respuesta = self.post(accion="crear", nombre="Combo", precio="6000.00",
                              imagen=(BytesIO(b"x" * (6 * 1024 * 1024)), "combo.png"))
        self.assertEqual(respuesta.status_code, 413)
        self.assertIn(b"5 MB", respuesta.data)
        self.assertNotIn(b"Request Entity Too Large", respuesta.data)
        self.assertFalse(any(metodo in ("POST", "PUT") for metodo, _, _ in self.llamadas))

    def test_descripcion_invalida_rechazada_por_validador_real(self):
        for descripcion in ("", "   ", "x" * 251):
            with self.subTest(descripcion=descripcion):
                respuesta = self.post(accion="crear", nombre="Agua", precio="2000.00", descripcion=descripcion)
                self.assertEqual(respuesta.status_code, 400)

    def test_descripcion_se_conserva_y_escapa_ante_error(self):
        self.escritura = ({"error": "El nombre ya existe"}, 409)
        respuesta = self.post(accion="editar", id_servicio="7", nombre="Agua", precio="2000.00", descripcion="<script>alert(1)</script>")
        self.assertEqual(respuesta.status_code, 409)
        self.assertIn(b"&lt;script&gt;alert(1)&lt;/script&gt;", respuesta.data)
        self.assertNotIn(b"<script>alert(1)</script>", respuesta.data)

    def test_error_al_crear_conserva_campos(self):
        self.escritura = ({"error": "El nombre ya existe"}, 409)
        respuesta = self.post(accion="crear", nombre="Agua duplicada", precio="2300.00")
        self.assertEqual(respuesta.status_code, 409)
        self.assertIn(b'value="Agua duplicada"', respuesta.data)
        self.assertIn(b'value="2300.00"', respuesta.data)
        self.assertIn(b"El nombre ya existe", respuesta.data)

    def test_error_al_editar_conserva_id_y_campos(self):
        self.escritura = ({"error": "El nombre ya existe"}, 409)
        respuesta = self.post(accion="editar", id_servicio="7", nombre="Nombre duplicado", precio="6200.00")
        self.assertEqual(respuesta.status_code, 409)
        self.assertIn(b'name="id_servicio" value="7"', respuesta.data)
        self.assertIn(b'value="Nombre duplicado"', respuesta.data)
        self.assertIn(b'value="6200.00"', respuesta.data)

    def test_fallo_listado_no_se_presenta_como_catalogo_vacio(self):
        self.listado = ({"error": "No se pudo conectar con el servidor"}, 503)
        respuesta = self.client.get("/admin/servicios")
        self.assertIn(b"No se pudo conectar con el servidor", respuesta.data)
        self.assertNotIn(b"Todav\xc3\xada no hay servicios", respuesta.data)

    def test_baja_rechazada_conserva_servicio_y_muestra_error(self):
        self.escritura = ({"error": "El servicio tiene compras asociadas"}, 409)
        respuesta = self.post(accion="eliminar", id_servicio="7")
        self.assertEqual(respuesta.status_code, 302)
        siguiente = self.client.get(respuesta.location)
        self.assertIn(b"El servicio tiene compras asociadas", siguiente.data)
        self.assertIn(b"Pochoclos", siguiente.data)
        self.assertIn(("DELETE", "/servicios/7", {}), self.llamadas)

    def test_edicion_inexistente_vuelve_al_listado(self):
        respuesta = self.client.get("/admin/servicios?editar=999")
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.location, "/admin/servicios")

    def test_sin_sesion_redirige_a_login(self):
        with self.client.session_transaction() as sesion:
            sesion.pop("backend_token")
        respuesta = self.client.get("/admin/servicios")
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(urlsplit(respuesta.location).path, "/login")
        self.assertEqual(parse_qs(urlsplit(respuesta.location).query)["next"], ["/admin/servicios"])
        self.assertFalse(self.llamadas)

    def test_cliente_no_accede(self):
        self.usuario["rol"] = "cliente"
        respuesta = self.client.get("/admin/servicios")
        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(any(ruta == "/servicios" for _, ruta, _ in self.llamadas))

    def test_sin_csrf_no_envia_operacion(self):
        respuesta = self.client.post("/admin/servicios", data={"accion": "eliminar", "id_servicio": "7"})
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(any(metodo != "GET" for metodo, _, _ in self.llamadas))


if __name__ == "__main__":
    unittest.main()
