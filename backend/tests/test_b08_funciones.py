import unittest
from unittest.mock import MagicMock, patch, ANY

from backend.app import app
from backend import seguridad
from backend.autenticacion import jwt
from flask_jwt_extended import create_access_token
from mysql.connector import Error as MySQLError
from backend.src.routes import funciones_routes as funciones
from backend.src.routes import peliculas_routes as peliculas
from backend.src.services import peliculas_service
from backend.src.services import funciones_service as servicio_funciones


class TestB08(unittest.TestCase):

    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="clave-test")
        self.client = app.test_client()
        bloqueo = patch.object(jwt, '_token_in_blocklist_callback', return_value=False)
        bloqueo.start()
        self.addCleanup(bloqueo.stop)

        # Simular la conexión que verifica los permisos de administrador.
        self.cn_seg = MagicMock()
        self.cur_seg = self.cn_seg.cursor.return_value
        self.cur_seg.__enter__.return_value = self.cur_seg
        self.cur_seg.fetchone.return_value = {
            "id_usuario": 8,
            "rol": "administrador",
        }

        self.parche_seg = patch.object(
            seguridad, "get_connection", return_value=self.cn_seg
        )
        self.parche_seg.start()
        self.addCleanup(self.parche_seg.stop)

        with app.app_context():
            token = create_access_token(identity="8")
        self.client.environ_base["HTTP_AUTHORIZATION"] = "Bearer " + token

    def base(self, modulo):
        cn = MagicMock()
        cur = cn.cursor.return_value
        cur.__enter__.return_value = cur
        cur.__exit__.return_value = False
        cur.fetchone.return_value = None
        cur.lastrowid = 37

        parche = patch.object(modulo, "get_connection", return_value=cn)
        parche.start()
        self.addCleanup(parche.stop)

        return cn, cur

    def pelicula_valida(self):
        return {
            "titulo": "Pelicula de prueba",
            "sinopsis": "Sinopsis de prueba",
            "poster": "poster.jpg",
            "duracion_minutos": 120,
            "clasificacion": "ATP",
            "genero": "Drama",
        }

    def funcion_valida(self):
        return {
            "id_pelicula": 1,
            "id_sala": 1,
            "fecha_hora_inicio": "2030-05-10T18:00:00",
            "precio_base": "5000.00",
        }

    # PELÍCULAS

    def test_listar_peliculas(self):
        with patch.object(
            peliculas_service, "obtener_peliculas", return_value=[]
        ):
            cn, _ = self.base(peliculas)
            respuesta = self.client.get("/api/peliculas")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json, {"peliculas": []})
        cn.close.assert_called_once()

    def test_crear_pelicula_correctamente(self):
        cn, cur = self.base(peliculas)

        respuesta = self.client.post(
            "/api/peliculas", json=self.pelicula_valida()
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json["id_pelicula"], 37)
        cn.commit.assert_called_once()
        cn.rollback.assert_not_called()
        self.assertEqual(
            cur.execute.call_args_list[0].args[1],
            ("Pelicula de prueba",),
        )
        cn.close.assert_called_once()

    def test_pelicula_invalida_no_se_guarda(self):
        datos = self.pelicula_valida()
        datos["duracion_minutos"] = True

        with patch.object(peliculas, "get_connection") as abrir:
            respuesta = self.client.post("/api/peliculas", json=datos)

        self.assertEqual(respuesta.status_code, 400)
        abrir.assert_not_called()

    def test_pelicula_duplicada_devuelve_409(self):
        cn, cur = self.base(peliculas)
        cur.fetchone.return_value = {"id_pelicula": 5}

        respuesta = self.client.post(
            "/api/peliculas", json=self.pelicula_valida()
        )

        self.assertEqual(respuesta.status_code, 409)
        cn.commit.assert_not_called()
        cn.rollback.assert_called_once()
        cn.close.assert_called_once()

    def test_error_de_base_de_datos_revierte_y_no_expone_detalles(self):
        cn, cur = self.base(peliculas)
        cur.execute.side_effect = MySQLError("detalle interno")

        respuesta = self.client.post(
            "/api/peliculas", json=self.pelicula_valida()
        )

        self.assertEqual(respuesta.status_code, 500)
        self.assertEqual(
            respuesta.json,
            {"error": "No se pudo guardar la película."},
        )
        cn.rollback.assert_called_once()
        cn.close.assert_called_once()

    def test_importar_pelicula_omdb_guarda_en_transaccion_de_la_ruta(self):
        cn, cur = self.base(peliculas)
        datos_omdb = {
            "id_imdb": "tt0068646",
            "titulo": "El padrino",
            "sinopsis": "Sinopsis",
            "poster": "poster.jpg",
            "duracion": "175 min",
            "clasificacion": "R",
            "genero": "Drama",
        }

        with patch.object(
            peliculas, "obtener_pelicula_por_id", return_value=datos_omdb
        ), patch.object(
            peliculas,
            "importar_pelicula_service",
            return_value={"exito": True, "id": 37, "accion": "insertada"},
        ) as guardar:
            respuesta = self.client.post(
                "/api/peliculas/omdb/importar",
                json={"imdb_id": "tt0068646"},
            )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json["id_pelicula"], 37)
        guardar.assert_called_once_with(
            cur,
            {
                "id_externo_api": "tt0068646",
                "titulo": "El padrino",
                "sinopsis": "Sinopsis",
                "poster": "poster.jpg",
                "duracion_minutos": 175,
                "clasificacion": "R",
                "genero": "Drama",
            },
        )
        cn.commit.assert_called_once()
        cn.close.assert_called_once()

    def test_modificar_pelicula_inexistente_devuelve_404(self):
        cn, cur = self.base(peliculas)
        cur.fetchone.return_value = None

        respuesta = self.client.put(
            "/api/peliculas/999", json=self.pelicula_valida()
        )

        self.assertEqual(respuesta.status_code, 404)
        cn.commit.assert_not_called()
        cn.rollback.assert_called_once()
        cn.close.assert_called_once()

    # FUNCIONES

    def test_listar_funciones(self):
        self.base(funciones)
        with patch.object(
            funciones,
            "listar_funciones_servicio",
            return_value=[],
        ):
            respuesta = self.client.get("/api/funciones")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json, [])

    def test_crear_funcion_correctamente(self):
        self.base(funciones)
        with patch.object(
            funciones, "crear_funcion_servicio", return_value=37
        ) as crear:
            respuesta = self.client.post(
                "/api/funciones", json=self.funcion_valida()
            )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json["id_funcion"], 37)
        crear.assert_called_once_with(ANY, self.funcion_valida())

    def test_crear_funcion_con_datos_invalidos(self):
        datos = self.funcion_valida()
        datos["precio_base"] = "-10"

        with patch.object(
            funciones, "crear_funcion_servicio"
        ) as crear:
            respuesta = self.client.post("/api/funciones", json=datos)

        self.assertEqual(respuesta.status_code, 400)
        crear.assert_not_called()

    def test_crear_funcion_con_pelicula_inexistente(self):
        self.base(funciones)
        with patch.object(
            funciones,
            "crear_funcion_servicio",
            side_effect=ValueError("La película especificada no existe."),
        ):
            respuesta = self.client.post(
                "/api/funciones", json=self.funcion_valida()
            )

        self.assertEqual(respuesta.status_code, 400)

    def test_ids_invalidos_se_rechazan_antes_de_modificar_funciones(self):
        valores_invalidos = (1.8, 1.0, True, None, "1", 0, -1, [], {})
        rutas = (("post", "/api/funciones"), ("put", "/api/funciones/1"))

        for metodo, ruta in rutas:
            for campo in ("id_pelicula", "id_sala"):
                for valor in valores_invalidos:
                    with self.subTest(metodo=metodo, campo=campo, valor=valor):
                        datos = self.funcion_valida()
                        datos[campo] = valor

                        with patch.object(funciones, "get_connection") as abrir, patch.object(
                            funciones, "crear_funcion_servicio"
                        ) as crear:
                            respuesta = getattr(self.client, metodo)(ruta, json=datos)

                        self.assertEqual(respuesta.status_code, 400, respuesta.json)
                        abrir.assert_not_called()
                        crear.assert_not_called()

    def test_modificar_funcion_con_datos_incompletos(self):
        respuesta = self.client.put(
            "/api/funciones/1",
            json={"id_pelicula": 1},
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_usuario_sin_sesion_no_puede_crear_pelicula(self):
        self.client.environ_base.pop("HTTP_AUTHORIZATION", None)
        with self.client.session_transaction() as sesion:
            sesion.clear()

        with patch.object(seguridad, "get_connection") as abrir:
            respuesta = self.client.post(
                "/api/peliculas", json=self.pelicula_valida()
            )

        self.assertEqual(respuesta.status_code, 401)
        abrir.assert_not_called()


    def test_usuario_sin_sesion_no_puede_crear_funcion(self):
        self.client.environ_base.pop("HTTP_AUTHORIZATION", None)
        with self.client.session_transaction() as sesion:
            sesion.clear()

        with patch.object(seguridad, "get_connection") as abrir:
            respuesta = self.client.post(
                "/api/funciones",
                json=self.funcion_valida(),
            )

        self.assertEqual(respuesta.status_code, 401)
        abrir.assert_not_called()

    def test_usuario_sin_sesion_no_puede_modificar_funcion(self):
        self.client.environ_base.pop("HTTP_AUTHORIZATION", None)
        with self.client.session_transaction() as sesion:
            sesion.clear()

        with patch.object(seguridad, "get_connection") as abrir:
            respuesta = self.client.put(
                "/api/funciones/1",
                json=self.funcion_valida(),
            )

        self.assertEqual(respuesta.status_code, 401)
        abrir.assert_not_called()

    def test_modificar_funcion_inexistente_devuelve_404(self):
        cn, cur = self.base(funciones)
        cur.fetchone.return_value = None

        respuesta = self.client.put(
            "/api/funciones/999",
            json=self.funcion_valida(),
        )

        self.assertEqual(respuesta.status_code, 404)
        cn.commit.assert_not_called()
        cn.close.assert_called_once()


    def test_modificar_pelicula_correctamente(self):
        cn, cur = self.base(peliculas)
        cur.fetchone.side_effect = [
            {"id_pelicula": 1, "duracion_minutos": "120"},
            None,
            None,
        ]

        respuesta = self.client.put(
            "/api/peliculas/1", json=self.pelicula_valida()
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json["id_pelicula"], 1)
        cn.commit.assert_called_once()
        cn.rollback.assert_not_called()
        cn.close.assert_called_once()

    def test_modificar_funcion_correctamente(self):
        from datetime import datetime

        cn, cur = self.base(funciones)
        cur.fetchone.side_effect = [
            {
                "id_funcion": 1,
                "id_pelicula": 1,
                "id_sala": 1,
                "fecha_hora_inicio": datetime(2030, 5, 10, 18, 0),
            },
            {"id_pelicula": 1},
            {"id_sala": 1},
            {"duracion_minutos": "120"},
        ]

        with patch.object(
            servicio_funciones, "contar_entradas_por_funcion", return_value=0
        ), patch.object(
            servicio_funciones, "obtener_funcion_por_id",
            return_value={
                "id_funcion": 1,
                "id_pelicula": 1,
                "id_sala": 1,
                "fecha_hora_inicio": datetime(2030, 5, 10, 18, 0),
            }
            ), patch.object(
            servicio_funciones, "obtener_pelicula_por_id",
            return_value={"id_pelicula": 1, "duracion_minutos": "120"}
            ), patch.object(
            servicio_funciones, "obtener_sala_por_id",
            return_value={"id_sala": 1}
            ), patch.object(
            servicio_funciones, "obtener_funciones_por_sala",
            return_value=[]
            ), patch.object(
            servicio_funciones, "modificar_funcion"
            ) as modificar:
            respuesta = self.client.put(
                "/api/funciones/1", json=self.funcion_valida()
            )       

        self.assertEqual(respuesta.status_code, 200, respuesta.json)
        self.assertEqual(respuesta.json["id_funcion"], 1)
        modificar.assert_called_once()
        cn.commit.assert_called_once()
        cn.close.assert_called_once()

    def test_modificar_funcion_rechaza_solapamiento(self):
        from datetime import datetime

        cn, cur = self.base(funciones)
        cur.fetchone.side_effect = [
            {
                "id_funcion": 1,
                "id_pelicula": 1,
                "id_sala": 1,
                "fecha_hora_inicio": datetime(2030, 5, 10, 18, 0),
            },
            {"id_pelicula": 1},
            {"id_sala": 1},
            {"duracion_minutos": "120"},
        ]

        with patch.object(
            servicio_funciones, "contar_entradas_por_funcion", return_value=0
        ), patch.object(
            servicio_funciones, "obtener_funcion_por_id",
            return_value={
                "id_funcion": 1,
                "id_pelicula": 1,
                "id_sala": 1,
                "fecha_hora_inicio": datetime(2030, 5, 10, 18, 0),
            }
        ), patch.object(
            servicio_funciones, "obtener_pelicula_por_id",
            return_value={"id_pelicula": 1, "duracion_minutos": "120"}
        ), patch.object(
            servicio_funciones, "obtener_sala_por_id",
            return_value={"id_sala": 1}
        ), patch.object(
            servicio_funciones, "obtener_funciones_por_sala",
            return_value=[{
                "id_funcion": 2,
                "fecha_hora_inicio": datetime(2030, 5, 10, 19, 0),
                "duracion_minutos": "120",
            }]
        ), patch.object(
            servicio_funciones, "modificar_funcion"
        ) as modificar:
            respuesta = self.client.put(
                "/api/funciones/1", json=self.funcion_valida()
            )

        self.assertEqual(respuesta.json["error"], "ERROR_VALIDACION")
        self.assertIn("sala", respuesta.json["mensaje"].lower())
        modificar.assert_not_called()
        cn.commit.assert_not_called()
        cn.close.assert_called_once()

    def test_calcular_solapamiento_real_de_horarios(self):
        from datetime import datetime
        from backend.src.services.funciones_service import (
        verificar_solapamiento_servicio,
        )

        cur = MagicMock()
        cur.fetchall.return_value = [{
            "id_funcion": 2,
            "fecha_hora_inicio": datetime(2030, 5, 10, 18, 0),
            "duracion_minutos": "120",
        }]

        se_solapan = verificar_solapamiento_servicio(
            cur, 1, datetime(2030, 5, 10, 19, 0), 90
        )

        self.assertTrue(se_solapan)

    def test_funciones_consecutivas_no_se_solapan(self):
        from datetime import datetime
        from backend.src.services.funciones_service import (
        verificar_solapamiento_servicio,
        )

        cur = MagicMock()
        cur.fetchall.return_value = [{
            "id_funcion": 2,
            "fecha_hora_inicio": datetime(2030, 5, 10, 18, 0),
            "duracion_minutos": "120",
        }]

        se_solapan = verificar_solapamiento_servicio(
            cur, 1, datetime(2030, 5, 10, 20, 0), 90
        )

        self.assertFalse(se_solapan)


    def test_modificar_funcion_con_entradas_vendidas_rechaza_cambio_de_horario(self):
        from datetime import datetime

        cn, cur = self.base(funciones)
        cur.fetchone.side_effect = [
            {
                "id_funcion": 1,
                "id_pelicula": 1,
                "id_sala": 1,
                "fecha_hora_inicio": datetime(2030, 5, 10, 18, 0),
            },
            {"id_pelicula": 1},
            {"id_sala": 1},
        ]

        datos = self.funcion_valida()
        datos["fecha_hora_inicio"] = "2030-05-10T20:00:00"

        with patch.object(
            servicio_funciones, "contar_entradas_por_funcion", return_value=5
        ), patch.object(
            servicio_funciones, "obtener_funcion_por_id",
            return_value={
                "id_funcion": 1,
                "id_pelicula": 1,
                "id_sala": 1,
                "fecha_hora_inicio": datetime(2030, 5, 10, 18, 0),
            }
        ), patch.object(
            servicio_funciones, "obtener_pelicula_por_id",
            return_value={"id_pelicula": 1, "duracion_minutos": "120"}
        ), patch.object(
            servicio_funciones, "obtener_sala_por_id",
            return_value={"id_sala": 1}
        ), patch.object(
            servicio_funciones, "modificar_funcion"
        ) as modificar:
            respuesta = self.client.put("/api/funciones/1", json=datos)

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json["error"], "ERROR_VALIDACION")
        modificar.assert_not_called()
        cn.commit.assert_not_called()
        cn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
