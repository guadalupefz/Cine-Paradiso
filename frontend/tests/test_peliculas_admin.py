import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SECRET_KEY", "clave-ficticia-para-pruebas-de-frontend-2026")
from frontend import app as frontend


class PeliculasAdmin(unittest.TestCase):
    def setUp(self):
        frontend.app.config.update(TESTING=True)
        self.client = frontend.app.test_client()
        self.usuario = {"id_usuario": 8, "nombre": "Admin", "rol": "administrador"}
        self.ficha = {"titulo": "Película de prueba", "sinopsis": "Una historia para probar el formulario.",
                      "poster": "/static/img/default.svg", "duracion_minutos": "108",
                      "clasificacion": "+13", "genero": "Drama"}
        self.peliculas = [{"id_pelicula": 7, **self.ficha}]
        self.listado = ({"peliculas": self.peliculas}, 200)
        self.resultado_externo = ({**self.ficha, "titulo": "Cinema Paradiso"}, 200)
        self.escritura = ({"mensaje": "Película guardada", "id_pelicula": 7}, 201)
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
        if metodo == "GET" and ruta == "/peliculas":
            return self.listado
        if ruta == "/pelicula":
            return self.resultado_externo
        return self.escritura

    def post(self, **datos):
        return self.client.post("/admin/peliculas", data={"csrf_token": "csrf-de-prueba", **datos})

    def test_catalogo_no_mezcla_formulario_de_alta(self):
        respuesta = self.client.get("/admin/peliculas")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Película de prueba", respuesta.text)
        self.assertIn('aria-label="Editar Película de prueba"', respuesta.text)
        self.assertNotIn('name="duracion_minutos"', respuesta.text)

    def test_alta_y_edicion_precargan_formulario(self):
        nuevo = self.client.get("/admin/peliculas?nuevo=1")
        self.assertIn('name="accion" value="crear"', nuevo.text)
        editar = self.client.get("/admin/peliculas?editar=7")
        self.assertIn('name="id_pelicula" value="7"', editar.text)
        self.assertIn('value="108"', editar.text)
        self.assertIn('value="Película de prueba"', editar.text)

    def test_crear_envia_duracion_entera_y_redirige(self):
        respuesta = self.post(accion="crear", **self.ficha)
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.location, "/admin/peliculas")
        esperados = {**self.ficha, "duracion_minutos": 108}
        self.assertIn(("POST", "/peliculas", {"json": esperados}), self.llamadas)

    def test_editar_conserva_id_y_datos_ante_rechazo(self):
        self.escritura = ({"error": "Tiene funciones programadas"}, 409)
        datos = {**self.ficha, "duracion_minutos": "115", "titulo": "Título corregido"}
        respuesta = self.post(accion="editar", id_pelicula="7", **datos)
        self.assertEqual(respuesta.status_code, 409)
        self.assertIn('name="id_pelicula" value="7"', respuesta.text)
        self.assertIn('value="115"', respuesta.text)
        self.assertIn('value="Título corregido"', respuesta.text)
        self.assertIn("Tiene funciones programadas", respuesta.text)
        self.assertTrue(any(metodo == "PUT" and ruta == "/peliculas/7" for metodo, ruta, _ in self.llamadas))

    def test_alta_rechazada_conserva_sinopsis_y_campos(self):
        self.escritura = ({"error": "Ya existe una película con ese título"}, 409)
        respuesta = self.post(accion="crear", **self.ficha)
        self.assertEqual(respuesta.status_code, 409)
        self.assertIn(self.ficha["sinopsis"], respuesta.text)
        self.assertIn('name="accion" value="crear"', respuesta.text)

    def test_error_base_conserva_formulario(self):
        self.escritura = ({"error": "No se pudo guardar la película"}, 500)
        respuesta = self.post(accion="crear", **self.ficha)
        self.assertEqual(respuesta.status_code, 500)
        self.assertIn('value="108"', respuesta.text)
        self.assertIn('role="alert"', respuesta.text)

    def test_buscar_no_importa_y_muestra_ficha(self):
        respuesta = self.post(accion="buscar", titulo="Cinema Paradiso")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Importar al catálogo", respuesta.text)
        self.assertIn("108 min", respuesta.text)
        self.assertIn(("GET", "/pelicula", {"params": {"titulo": "Cinema Paradiso"}}), self.llamadas)
        self.assertFalse(any(m == "POST" for m, _, _ in self.llamadas))

    def test_importar_usa_titulo_consultado_y_redirige(self):
        self.resultado_externo = ({"mensaje": "Película importada"}, 200)
        respuesta = self.post(accion="importar", titulo="Cinema Paradiso")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(("POST", "/pelicula", {"params": {"titulo": "Cinema Paradiso"}}), self.llamadas)

    def test_importacion_duplicada_legacy_no_anuncia_exito(self):
        self.resultado_externo = ({" Error": "La película ya se encuentra cargada"}, 200)
        respuesta = self.post(accion="importar", titulo="Cinema Paradiso")
        self.assertEqual(respuesta.status_code, 409)
        self.assertIn("La película ya se encuentra cargada", respuesta.text)
        self.assertNotIn('class="aviso ok"', respuesta.text)
        self.assertIn('value="Cinema Paradiso"', respuesta.text)

    def test_api_no_disponible_conserva_busqueda_y_ofrece_carga_manual(self):
        self.resultado_externo = ({"error": "La API externa no está configurada"}, 503)
        respuesta = self.post(accion="buscar", titulo="Cinema Paradiso")
        self.assertEqual(respuesta.status_code, 503)
        self.assertIn('value="Cinema Paradiso"', respuesta.text)
        self.assertIn("cargar la película manualmente", respuesta.text)
        self.assertNotIn("Importar al catálogo", respuesta.text)

    def test_respuesta_externa_incompleta_muestra_error(self):
        self.resultado_externo = ({"mensaje": "Sin ficha"}, 200)
        respuesta = self.post(accion="buscar", titulo="Prueba")
        self.assertEqual(respuesta.status_code, 502)
        self.assertIn("no devolvió una ficha", respuesta.text)

    def test_titulo_vacio_no_consulta_proveedor(self):
        respuesta = self.post(accion="buscar", titulo="   ")
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(any(ruta == "/pelicula" for _, ruta, _ in self.llamadas))

    def test_fallo_listado_no_parece_catalogo_vacio(self):
        self.listado = ({"error": "Servidor no disponible"}, 503)
        respuesta = self.client.get("/admin/peliculas")
        self.assertIn("No pudimos cargar el catálogo", respuesta.text)
        self.assertNotIn("No hay películas cargadas.", respuesta.text)

    def test_edicion_inexistente_redirige(self):
        respuesta = self.client.get("/admin/peliculas?editar=999")
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.location, "/admin/peliculas")

    def test_edicion_sin_id_no_llama_api_de_escritura(self):
        respuesta = self.post(accion="editar", **self.ficha)
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(any(m != "GET" for m, _, _ in self.llamadas))

    def test_no_admin_ni_sin_sesion_acceden(self):
        self.usuario["rol"] = "cliente"
        self.assertEqual(self.client.get("/admin/peliculas").status_code, 403)
        with self.client.session_transaction() as sesion:
            sesion.pop("backend_token")
        self.assertEqual(self.client.get("/admin/peliculas").status_code, 302)

    def test_falta_csrf_impide_escritura(self):
        respuesta = self.client.post("/admin/peliculas", data={"accion": "crear", **self.ficha})
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(any(m != "GET" for m, _, _ in self.llamadas))

    def test_escape_de_texto_y_poster_no_web(self):
        self.peliculas[0].update(titulo='<script>alert("x")</script>', poster="javascript:alert(1)")
        respuesta = self.client.get("/admin/peliculas")
        self.assertNotIn('<script>alert("x")</script>', respuesta.text)
        self.assertNotIn('src="javascript:', respuesta.text)
        self.assertIn("poster_sin_imagen.svg", respuesta.text)


if __name__ == "__main__":
    unittest.main()
