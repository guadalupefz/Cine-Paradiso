import unittest
from unittest.mock import MagicMock, patch

from flask_jwt_extended import create_access_token

from backend import seguridad
from backend.app import app
from backend.autenticacion import jwt
from backend.src.routes import resenas_routes
from backend.src.services import resenas_service


class RutasResenasTest(unittest.TestCase):
    def setUp(self):
        app.config.update(
            TESTING=True,
            SECRET_KEY="clave-de-prueba-resenas-1234567890",
            JWT_SECRET_KEY="clave-de-prueba-resenas-1234567890",
        )
        self.client = app.test_client()
        self.usuario = {"id_usuario": 8, "rol": "cliente"}
        self.conexion_seguridad = MagicMock()
        cursor = self.conexion_seguridad.cursor.return_value
        cursor.__enter__.return_value = cursor
        cursor.fetchone.return_value = self.usuario
        parche_seguridad = patch.object(
            seguridad,
            "get_connection",
            return_value=self.conexion_seguridad,
        )
        parche_seguridad.start()
        self.addCleanup(parche_seguridad.stop)

        parche_blocklist = patch.object(
            jwt, "_token_in_blocklist_callback", return_value=False
        )
        parche_blocklist.start()
        self.addCleanup(parche_blocklist.stop)

        with app.app_context():
            token = create_access_token(identity="8")
        self.client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"

    def test_listar_resenas_es_publico(self):
        resultado = {
            "pelicula": {"id_pelicula": 3, "titulo": "Película"},
            "cantidad": 1,
            "promedio": 4.0,
            "resenas": [],
        }
        with patch.object(
            resenas_routes.resenas_service,
            "obtener_resenas_pelicula",
            return_value=resultado,
        ):
            self.client.environ_base.pop("HTTP_AUTHORIZATION", None)
            respuesta = self.client.get("/api/peliculas/3/resenas")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json, resultado)

    def test_guardar_resena_valida_y_delega_al_servicio(self):
        with patch.object(
            resenas_routes.resenas_service,
            "guardar_resena",
            return_value=({"mensaje": "Guardada"}, None, 200),
        ) as guardar:
            respuesta = self.client.post(
                "/api/peliculas/3/resenas",
                json={"puntuacion": 5, "comentario": "Muy buena"},
            )

        self.assertEqual(respuesta.status_code, 200)
        guardar.assert_called_once_with(8, 3, 5, "Muy buena")

    def test_cliente_consulta_su_elegibilidad_y_resena(self):
        propia = {
            "puede_resenar": True,
            "puntuacion": 4,
            "comentario": "Buena",
            "fecha_actualizacion": "2026-11-14",
        }
        with patch.object(
            resenas_routes.resenas_service,
            "obtener_resena_propia",
            return_value=propia,
        ):
            respuesta = self.client.get("/api/peliculas/3/resenas/propia")

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json["puede_resenar"])
        self.assertEqual(respuesta.json["resena"]["puntuacion"], 4)

    def test_puntuacion_fuera_de_rango_no_se_guarda(self):
        with patch.object(resenas_routes.resenas_service, "guardar_resena") as guardar:
            respuesta = self.client.post(
                "/api/peliculas/3/resenas",
                json={"puntuacion": 6, "comentario": ""},
            )

        self.assertEqual(respuesta.status_code, 400)
        guardar.assert_not_called()

    def test_comentario_mayor_a_1000_caracteres_se_rechaza(self):
        respuesta = self.client.post(
            "/api/peliculas/3/resenas",
            json={"puntuacion": 3, "comentario": "x" * 1001},
        )
        self.assertEqual(respuesta.status_code, 400)

    def test_solo_cliente_puede_publicar(self):
        self.usuario["rol"] = "administrador"
        with patch.object(resenas_routes.resenas_service, "guardar_resena") as guardar:
            respuesta = self.client.post(
                "/api/peliculas/3/resenas",
                json={"puntuacion": 3, "comentario": ""},
            )

        self.assertEqual(respuesta.status_code, 403)
        guardar.assert_not_called()


class ServicioResenasTest(unittest.TestCase):
    def conexion_falsa(self):
        conexion = MagicMock()
        cursor = conexion.cursor.return_value
        cursor.__enter__.return_value = cursor
        cursor.__exit__.return_value = False
        return conexion

    def test_usuario_sin_asistencia_qr_no_puede_resenar(self):
        conexion = self.conexion_falsa()
        with patch.object(resenas_service, "get_connection", return_value=conexion), \
             patch.object(
                 resenas_service.repo,
                 "obtener_resumen_resenas",
                 return_value={"id_pelicula": 3, "titulo": "Película"},
             ), \
             patch.object(
                 resenas_service.repo,
                 "tiene_asistencia_validada",
                 return_value=False,
             ), \
             patch.object(resenas_service.repo, "guardar_resena") as guardar:
            resultado, error, estado = resenas_service.guardar_resena(
                8, 3, 4, "Buena"
            )

        self.assertIsNone(resultado)
        self.assertIsInstance(error, str)
        if error is None:
            self.fail("Se esperaba un error de elegibilidad.")
        self.assertIn("validadas por QR", error)
        self.assertEqual(estado, 403)
        conexion.rollback.assert_called_once()
        conexion.commit.assert_not_called()
        guardar.assert_not_called()
        conexion.close.assert_called_once()

    def test_asistencia_validada_permite_crear_o_editar_resena(self):
        conexion = self.conexion_falsa()
        with patch.object(resenas_service, "get_connection", return_value=conexion), \
             patch.object(
                 resenas_service.repo,
                 "obtener_resumen_resenas",
                 return_value={"id_pelicula": 3, "titulo": "Película"},
             ), \
             patch.object(
                 resenas_service.repo,
                 "tiene_asistencia_validada",
                 return_value=True,
             ), \
             patch.object(resenas_service.repo, "guardar_resena") as guardar:
            resultado, error, estado = resenas_service.guardar_resena(
                8, 3, 4, "Buena"
            )

        self.assertEqual(estado, 200)
        self.assertIsNone(error)
        if resultado is None:
            self.fail("Se esperaba una respuesta de guardado.")
        self.assertEqual(resultado["mensaje"], "La reseña se guardó correctamente.")
        guardar.assert_called_once_with(conexion.cursor.return_value, 8, 3, 4, "Buena")
        conexion.commit.assert_called_once()
        conexion.rollback.assert_not_called()
        conexion.close.assert_called_once()

    def test_repositorio_exige_marca_de_validacion_qr(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = {"1": 1}
        from backend.src.repositories import resenas_repository

        resenas_repository.tiene_asistencia_validada(cursor, 8, 3)
        consulta = cursor.execute.call_args.args[0]
        self.assertIn("fecha_hora_validacion IS NOT NULL", consulta)
        self.assertIn("c.estado = 'confirmada'", consulta)


if __name__ == "__main__":
    unittest.main()
