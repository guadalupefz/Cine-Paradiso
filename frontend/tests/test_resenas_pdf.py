import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SECRET_KEY", "clave-ficticia-para-pruebas-de-frontend-2026")
from frontend import app as frontend


class ResenasYPdfTest(unittest.TestCase):
    def setUp(self):
        frontend.app.config.update(TESTING=True)
        self.client = frontend.app.test_client()
        self.usuario = {"id_usuario": 8, "nombre": "Cliente", "rol": "cliente"}
        self.resenas = {
            "pelicula": {"id_pelicula": 3, "titulo": "Película de prueba"},
            "cantidad": 1,
            "promedio": 4.0,
            "resenas": [{
                "puntuacion": 4,
                "comentario": "Me gustó",
                "fecha_actualizacion": "2026-11-14",
            }],
        }
        self.propia = {
            "puede_resenar": True,
            "resena": {"puntuacion": 4, "comentario": "Me gustó"},
        }
        self.ventas = {
            "ventas_por_genero": [{
                "genero": "Drama",
                "entradas_vendidas": 12,
                "importe_estimado_entradas": "60000.00",
            }],
            "ventas_por_franja_horaria": [{
                "franja_horaria": "Noche",
                "entradas_vendidas": 12,
                "importe_estimado_entradas": "60000.00",
            }],
            "cantidad_cancelaciones": 2,
        }
        self.ocupacion = {
            "ocupacion_por_funcion": [{
                "pelicula": "Película de prueba",
                "fecha_hora_inicio": "2026-11-14 20:00",
                "sala": "Sala 1",
                "butacas_ocupadas": 12,
                "capacidad": 100,
                "porcentaje_ocupacion": 12,
            }],
            "ocupacion_por_pelicula": [{
                "pelicula": "Película de prueba",
                "butacas_ocupadas": 12,
                "capacidad_total": 100,
                "porcentaje_ocupacion": 12,
            }],
        }
        self.llamadas = []
        with self.client.session_transaction() as sesion:
            sesion.update(
                backend_token="token-de-prueba",
                csrf_token="csrf-de-prueba",
            )
        parche = patch.object(
            frontend, "llamar_backend", side_effect=self.responder_backend
        )
        parche.start()
        self.addCleanup(parche.stop)

    def responder_backend(self, metodo, ruta, **argumentos):
        self.llamadas.append((metodo, ruta, argumentos))
        if ruta == "/usuarios/me":
            return self.usuario, 200
        if ruta == "/peliculas/3/resenas":
            return self.resenas, 200
        if ruta == "/peliculas/3/resenas/propia":
            return self.propia, 200
        if ruta == "/estadisticas/ventas":
            return self.ventas, 200
        if ruta == "/estadisticas/ocupacion":
            return self.ocupacion, 200
        if metodo == "POST":
            return {"mensaje": "La reseña se guardó correctamente."}, 200
        return {}, 404

    def test_pagina_publica_muestra_promedio_y_opiniones(self):
        with self.client.session_transaction() as sesion:
            sesion.pop("backend_token")

        respuesta = self.client.get("/peliculas/3/resenas")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("4.0/5", respuesta.text)
        self.assertIn("Me gustó", respuesta.text)

    def test_cliente_puede_editar_su_resena_si_tuvo_asistencia_validada(self):
        respuesta = self.client.get("/peliculas/3/resenas")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Actualizar reseña", respuesta.text)
        self.assertIn("name=\"puntuacion\"", respuesta.text)

    def test_formulario_envia_puntuacion_y_comentario_al_backend(self):
        respuesta = self.client.post(
            "/peliculas/3/resenas",
            data={
                "csrf_token": "csrf-de-prueba",
                "puntuacion": "5",
                "comentario": "Excelente",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        llamada = next(
            llamada for llamada in self.llamadas
            if llamada[0] == "POST" and llamada[1] == "/peliculas/3/resenas"
        )
        self.assertEqual(
            llamada[2]["json"],
            {"puntuacion": 5, "comentario": "Excelente"},
        )

    def test_cliente_sin_asistencia_no_ve_formulario(self):
        self.propia = {"puede_resenar": False, "resena": None}
        respuesta = self.client.get("/peliculas/3/resenas")
        self.assertIn("debe validarse una entrada", respuesta.text)
        self.assertNotIn("<button type=\"submit\">Publicar reseña", respuesta.text)

    def test_descarga_informe_pdf_con_metricas_de_ventas_y_ocupacion(self):
        self.usuario["rol"] = "administrador"
        respuesta = self.client.get("/admin/estadisticas/pdf")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.mimetype, "application/pdf")
        disposicion = respuesta.headers.get("Content-Disposition")
        self.assertIsNotNone(disposicion)
        if disposicion is None:
            self.fail("El informe debe descargarse como archivo adjunto.")
        self.assertTrue(disposicion.startswith("attachment;"))
        self.assertTrue(respuesta.data.startswith(b"%PDF-"))
        self.assertIn(("GET", "/estadisticas/ventas", {}), self.llamadas)
        self.assertIn(("GET", "/estadisticas/ocupacion", {}), self.llamadas)

    def test_cliente_no_puede_descargar_informe_administrativo(self):
        respuesta = self.client.get("/admin/estadisticas/pdf")
        self.assertEqual(respuesta.status_code, 403)

    def test_error_de_metricas_no_descarga_un_pdf_vacio(self):
        self.usuario["rol"] = "administrador"

        def responder_con_error(metodo, ruta, **argumentos):
            if ruta == "/usuarios/me":
                return self.usuario, 200
            if ruta == "/estadisticas/ventas":
                return {"mensaje": "Backend sin conexión"}, 503
            if ruta == "/estadisticas/ocupacion":
                return self.ocupacion, 200
            return {}, 404

        with patch.object(
            frontend, "llamar_backend", side_effect=responder_con_error
        ):
            respuesta = self.client.get(
                "/admin/estadisticas/pdf", follow_redirects=True
            )

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("No se pudo generar el informe", respuesta.text)
        self.assertNotEqual(respuesta.mimetype, "application/pdf")


if __name__ == "__main__":
    unittest.main()
