import unittest
from unittest.mock import MagicMock, patch

from backend.app import app
from backend import seguridad
from backend.src.routes import funciones_routes as funciones
from backend.src.routes import peliculas_routes as peliculas


class TestB08(unittest.TestCase):

    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="clave-test")
        self.client = app.test_client()

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

        with self.client.session_transaction() as sesion:
            sesion["id_usuario"] = 8

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
            peliculas, "obtener_peliculas", return_value=[]
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
        cn.close.assert_called_once()

    def test_modificar_pelicula_inexistente_devuelve_404(self):
        cn, cur = self.base(peliculas)
        cur.fetchone.return_value = None

        respuesta = self.client.put(
            "/api/peliculas/999", json=self.pelicula_valida()
        )

        self.assertEqual(respuesta.status_code, 404)
        cn.commit.assert_not_called()
        cn.close.assert_called_once()

    # FUNCIONES

    def test_listar_funciones(self):
        with patch.object(
            funciones,
            "listar_funciones_servicio",
            return_value=[],
        ):
            respuesta = self.client.get("/api/funciones")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json, [])

    def test_crear_funcion_correctamente(self):
        with patch.object(
            funciones, "crear_funcion_servicio", return_value=37
        ) as crear:
            respuesta = self.client.post(
                "/api/funciones", json=self.funcion_valida()
            )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json["id_funcion"], 37)
        crear.assert_called_once_with(self.funcion_valida())

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
        with patch.object(
            funciones,
            "crear_funcion_servicio",
            side_effect=ValueError("La película especificada no existe."),
        ):
            respuesta = self.client.post(
                "/api/funciones", json=self.funcion_valida()
            )

        self.assertEqual(respuesta.status_code, 400)

    def test_modificar_funcion_con_datos_incompletos(self):
        respuesta = self.client.put(
            "/api/funciones/1",
            json={"id_pelicula": 1},
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_usuario_sin_sesion_no_puede_crear_pelicula(self):
        with self.client.session_transaction() as sesion:
            sesion.clear()

        with patch.object(seguridad, "get_connection") as abrir:
            respuesta = self.client.post(
                "/api/peliculas", json=self.pelicula_valida()
            )

        self.assertEqual(respuesta.status_code, 401)
        abrir.assert_not_called()


    def test_usuario_sin_sesion_no_puede_crear_funcion(self):
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
        cur.fetchone.return_value = {"id_pelicula": 1}

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
                "id_sala": 1,
                "fecha_hora_inicio": datetime(2030, 5, 10, 18, 0),
            },
            {"id_pelicula": 1},
            {"id_sala": 1},
            {"duracion_minutos": "120"},
        ]

        with patch.object(
            funciones, "contar_entradas_por_funcion", return_value=0
        ), patch.object(
            funciones, "verificar_solapamiento_sala", return_value=False
        ), patch.object(funciones, "modificar_funcion") as modificar:
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
                "id_sala": 1,
                "fecha_hora_inicio": datetime(2030, 5, 10, 18, 0),
            },
            {"id_pelicula": 1},
            {"id_sala": 1},
            {"duracion_minutos": "120"},
        ]

        with patch.object(
            funciones, "contar_entradas_por_funcion", return_value=0
        ), patch.object(
            funciones, "verificar_solapamiento_sala", return_value=True
        ), patch.object(funciones, "modificar_funcion") as modificar:
            respuesta = self.client.put(
                "/api/funciones/1", json=self.funcion_valida()
            )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(
            respuesta.json["error"], "SOLAPAMIENTO_HORARIO"
        )
        modificar.assert_not_called()
        cn.commit.assert_not_called()
        cn.close.assert_called_once()

    def test_calcular_solapamiento_real_de_horarios(self):
        from datetime import datetime
        from backend.src.repositories.funciones_repository import (
            verificar_solapamiento_sala,
        )

        cur = MagicMock()
        cur.fetchall.return_value = [{
            "id_funcion": 2,
            "fecha_hora_inicio": datetime(2030, 5, 10, 18, 0),
            "duracion_minutos": "120",
        }]

        se_solapan = verificar_solapamiento_sala(
            cur, 1, datetime(2030, 5, 10, 19, 0), 90
        )

        self.assertTrue(se_solapan)

    def test_funciones_consecutivas_no_se_solapan(self):
        from datetime import datetime
        from backend.src.repositories.funciones_repository import (
            verificar_solapamiento_sala,
        )

        cur = MagicMock()
        cur.fetchall.return_value = [{
            "id_funcion": 2,
            "fecha_hora_inicio": datetime(2030, 5, 10, 18, 0),
            "duracion_minutos": "120",
        }]

        se_solapan = verificar_solapamiento_sala(
            cur, 1, datetime(2030, 5, 10, 20, 0), 90
        )

        self.assertFalse(se_solapan)


    def test_modificar_funcion_con_entradas_vendidas_rechaza_cambio_de_horario(self):
        from datetime import datetime

        cn, cur = self.base(funciones)
        cur.fetchone.side_effect = [
            {
                "id_funcion": 1,
                "id_sala": 1,
                "fecha_hora_inicio": datetime(2030, 5, 10, 18, 0),
            },
            {"id_pelicula": 1},
            {"id_sala": 1},
        ]

        datos = self.funcion_valida()
        datos["fecha_hora_inicio"] = "2030-05-10T20:00:00"

        with patch.object(
            funciones, "contar_entradas_por_funcion", return_value=5
        ), patch.object(funciones, "modificar_funcion") as modificar:
            respuesta = self.client.put("/api/funciones/1", json=datos)

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json["error"], "RESTRICCION_VENTAS")
        modificar.assert_not_called()
        cn.commit.assert_not_called()
        cn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
