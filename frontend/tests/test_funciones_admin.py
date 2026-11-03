import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SECRET_KEY", "clave-ficticia-para-pruebas-de-frontend-2026")
from frontend import app as frontend


class FuncionesAdmin(unittest.TestCase):
    def setUp(self):
        frontend.app.config.update(TESTING=True)
        self.client = frontend.app.test_client()
        self.usuario = {"id_usuario": 8, "nombre": "Admin", "rol": "administrador"}
        self.peliculas = [{"id_pelicula": 5, "titulo": "Película de prueba", "duracion_minutos": 108}]
        self.funciones = [{"id_funcion": 21, "id_pelicula": 5, "id_sala": 7,
                           "titulo": "Película de prueba", "sala_nombre": "Sala azul",
                           "fecha_hora_inicio": "Wed, 04 Nov 2026 20:00:37 GMT", "precio_base": "8000.00"}]
        self.locales = [{"id_local": 3, "nombre": "Centro"}, {"id_local": 4, "nombre": "Norte"}]
        self.salas = {3: [{"id_sala": 7, "nombre": "Sala azul", "capacidad": 100}],
                      4: [{"id_sala": 8, "nombre": "Sala roja", "capacidad": 80}]}
        self.errores = {}
        self.escritura = ({"mensaje": "Función guardada", "id_funcion": 21}, 201)
        self.llamadas = []
        self.datos = {"id_pelicula": "5", "id_sala": "7", "fecha_hora_inicio": "2026-11-04T20:00:37", "precio_base": "8000.00"}
        with self.client.session_transaction() as sesion:
            sesion.update(backend_token="token-de-prueba", csrf_token="csrf-de-prueba")
        parche = patch.object(frontend, "llamar_backend", side_effect=self.backend)
        parche.start()
        self.addCleanup(parche.stop)

    def backend(self, metodo, ruta, **argumentos):
        self.llamadas.append((metodo, ruta, argumentos))
        if ruta == "/usuarios/me":
            return self.usuario, 200
        if metodo != "GET":
            return self.escritura
        if ruta in self.errores:
            return {"error": "No disponible"}, self.errores[ruta]
        if ruta == "/peliculas": return {"peliculas": self.peliculas}, 200
        if ruta == "/funciones": return self.funciones, 200
        if ruta == "/locales": return {"locales": self.locales}, 200
        return {"salas": self.salas[int(ruta.split('/')[2])]}, 200

    def post(self, **datos):
        return self.client.post("/admin/funciones", data={"csrf_token": "csrf-de-prueba", **datos})

    def test_alta_usa_ids_enteros_y_precio_texto(self):
        respuesta = self.post(**self.datos)
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(("POST", "/funciones", {"json": {**self.datos, "id_pelicula": 5, "id_sala": 7}}), self.llamadas)

    def test_edicion_usa_put_al_identificador(self):
        self.escritura = ({"mensaje": "Función modificada"}, 200)
        respuesta = self.post(id_funcion="21", **self.datos)
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(any(metodo == "PUT" and ruta == "/funciones/21" for metodo, ruta, _ in self.llamadas))

    def test_solapamiento_conserva_datos_del_alta(self):
        self.escritura = ({"error": "La sala ya se encuentra ocupada"}, 400)
        respuesta = self.post(**self.datos)
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("La sala ya se encuentra ocupada", respuesta.text)
        self.assertIn('value="2026-11-04T20:00:37"', respuesta.text)
        self.assertIn('value="8000.00"', respuesta.text)
        self.assertIn('value="7" selected', respuesta.text)

    def test_restriccion_ventas_conserva_id_edicion(self):
        self.escritura = ({"error": "RESTRICCION_VENTAS", "mensaje": "Ya existen entradas vendidas"}, 400)
        respuesta = self.post(id_funcion="21", **self.datos)
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('name="id_funcion" value="21"', respuesta.text)
        self.assertIn("Ya existen entradas vendidas", respuesta.text)

    def test_error_de_base_conserva_formulario(self):
        self.escritura = ({"error": "No se pudo guardar la función"}, 500)
        respuesta = self.post(**self.datos)
        self.assertEqual(respuesta.status_code, 500)
        self.assertIn('value="8000.00"', respuesta.text)

    def test_edicion_no_trunca_segundos_del_horario(self):
        respuesta = self.client.get("/admin/funciones?editar=21")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('value="2026-11-04T20:00:37"', respuesta.text)

    def test_fecha_iso_se_carga_en_edicion(self):
        self.funciones[0]["fecha_hora_inicio"] = "2026-11-04T20:00:37"
        respuesta = self.client.get("/admin/funciones?editar=21")
        self.assertIn('value="2026-11-04T20:00:37"', respuesta.text)

    def test_edicion_ausente_redirige(self):
        respuesta = self.client.get("/admin/funciones?editar=999")
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.location, "/admin/funciones")

    def test_id_edicion_invalido_no_crea_por_accidente(self):
        for identificador in ("", "abc", "0", "-1", "1.5"):
            with self.subTest(identificador=identificador):
                respuesta = self.post(id_funcion=identificador, **self.datos)
                self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(any(metodo != "GET" for metodo, _, _ in self.llamadas))

    def test_ids_decimales_no_se_truncan(self):
        self.escritura = ({"error": "IDs inválidos"}, 400)
        respuesta = self.post(**{**self.datos, "id_sala": "7.5"})
        self.assertEqual(respuesta.status_code, 400)
        enviada = next(argumentos["json"] for metodo, _, argumentos in self.llamadas if metodo == "POST")
        self.assertIsNone(enviada["id_sala"])

    def test_fallo_de_salas_de_un_local_es_visible(self):
        self.errores["/locales/4/salas"] = 500
        respuesta = self.client.get("/admin/funciones?nuevo=1")
        self.assertIn("No se pudieron cargar las salas de Norte.", respuesta.text)
        self.assertIn("disabled", respuesta.text)

    def test_fallo_listado_no_se_confunde_con_lista_vacia(self):
        self.errores["/funciones"] = 500
        respuesta = self.client.get("/admin/funciones")
        self.assertIn("No se pudieron cargar las funciones programadas.", respuesta.text)
        self.assertNotIn("No hay funciones programadas.", respuesta.text)

    def test_salas_de_distintos_locales_conservan_nombre_local(self):
        respuesta = self.client.get("/admin/funciones?nuevo=1")
        self.assertIn("Centro · Sala azul", respuesta.text)
        self.assertIn("Norte · Sala roja", respuesta.text)

    def test_sin_sesion_y_cliente_no_acceden(self):
        self.usuario["rol"] = "cliente"
        self.assertEqual(self.client.get("/admin/funciones").status_code, 403)
        with self.client.session_transaction() as sesion:
            sesion.pop("backend_token")
        self.assertEqual(self.client.get("/admin/funciones").status_code, 302)

    def test_sin_csrf_no_envia_escritura(self):
        respuesta = self.client.post("/admin/funciones", data=self.datos)
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(any(metodo != "GET" for metodo, _, _ in self.llamadas))


if __name__ == "__main__":
    unittest.main()
