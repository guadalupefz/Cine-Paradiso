import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SECRET_KEY", "clave-ficticia-para-pruebas-de-frontend-2026")
os.environ.setdefault("BACKEND_URL", "http://127.0.0.1:5001/api")

from frontend.app import app


class BaseTestCase(unittest.TestCase):
    """Clase base para configurar el cliente de pruebas de Flask."""

    CSRF_TOKEN = "csrf-test-token"

    def setUp(self):
        app.config.update(
            TESTING=True,
            SECRET_KEY="clave-ficticia-para-pruebas-de-frontend-2026"
        )
        self.client = app.test_client()
        with self.client.session_transaction() as sesion:
            sesion["csrf_token"] = self.CSRF_TOKEN

        self.usuario_cliente = {
            "id_usuario": 8,
            "nombre": "Cliente Test",
            "apellido": "Usuario",
            "email": "cliente@example.com",
            "rol": "cliente"
        }
        self.usuario_admin = {
            "id_usuario": 1,
            "nombre": "Admin Test",
            "apellido": "Sistema",
            "email": "admin@example.com",
            "rol": "administrador"
        }

    def post(self, url, data=None, **kwargs):
        """Helper para peticiones POST que inyecta automáticamente el csrf_token."""
        data_dict = dict(data) if data else {}
        data_dict.setdefault("csrf_token", self.CSRF_TOKEN)
        return self.client.post(url, data=data_dict, **kwargs)

    def establecer_sesion(self, token="token-jwt-valido"):
        """Simula una sesión de usuario autenticado."""
        with self.client.session_transaction() as sesion:
            sesion["backend_token"] = token
            sesion["csrf_token"] = self.CSRF_TOKEN


class TestPublicRoutes(BaseTestCase):
    """Pruebas para las rutas públicas (Cartelera, Funciones y Reseñas)."""

    @patch("frontend.routes.public_routes.llamar_backend")
    def test_cartelera_index_200(self, mock_backend):
        mock_backend.return_value = (
            {
                "peliculas": [
                    {
                        "id_pelicula": 1,
                        "titulo": "Cine Paradiso",
                        "duracion_minutos": 124,
                        "poster": "static/img/demo.jpg"
                    }
                ]
            },
            200
        )
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Cine Paradiso", response.data)

    @patch("frontend.routes.public_routes.llamar_backend")
    def test_ver_funciones_filtro_pelicula(self, mock_backend):
        mock_backend.return_value = (
            {
                "cartelera": [
                    {
                        "id_funcion": 10,
                        "id_pelicula": 1,
                        "titulo": "Cine Paradiso",
                        "fecha_hora_inicio": "Fri, 20 Nov 2026 20:00:00 GMT",
                        "sala_nombre": "Sala 1",
                        "precio_base": 4500
                    }
                ]
            },
            200
        )
        response = self.client.get("/funciones?id_pelicula=1")
        self.assertEqual(response.status_code, 200)

    @patch("frontend.utils.auth_helpers.llamar_backend")
    @patch("frontend.routes.public_routes.llamar_backend")
    def test_ver_resenas_pelicula_get(self, mock_backend_public, mock_backend_auth):
        mock_backend_auth.return_value = (self.usuario_cliente, 200)
        mock_backend_public.side_effect = [
            ({"resenas": []}, 200),
            ({"comentario": "Excelente"}, 200)
        ]
        self.establecer_sesion()
        response = self.client.get("/peliculas/1/resenas")
        self.assertEqual(response.status_code, 200)


class TestAuthRoutes(BaseTestCase):
    """Pruebas para las rutas de Autenticación (Login, Registro y Logout)."""

    @patch("frontend.routes.auth_routes.llamar_backend")
    def test_registro_contrasenas_no_coinciden(self, mock_backend):
        response = self.post("/registro", data={
            "nombre": "Test",
            "apellido": "User",
            "email": "test@example.com",
            "password": "Password1!",
            "confirmar_password": "Password2!"
        })
        self.assertEqual(response.status_code, 400)
        mock_backend.assert_not_called()

    @patch("frontend.routes.auth_routes.llamar_backend")
    def test_registro_exitoso(self, mock_backend):
        mock_backend.return_value = ({"mensaje": "Usuario creado"}, 201)
        response = self.post("/registro", data={
            "nombre": "Test",
            "apellido": "User",
            "email": "test@example.com",
            "password": "Password123!",
            "confirmar_password": "Password123!"
        })
        self.assertEqual(response.status_code, 302)

    @patch("frontend.routes.auth_routes.llamar_backend")
    def test_login_exitoso_guarda_token(self, mock_backend):
        mock_backend.return_value = (
            {
                "access_token": "token-jwt-ficticio",
                "usuario": self.usuario_cliente
            },
            200
        )
        response = self.post("/login", data={
            "email": "cliente@example.com",
            "password": "Password123!"
        })
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as sesion:
            self.assertEqual(sesion.get("backend_token"), "token-jwt-ficticio")

    @patch("frontend.routes.auth_routes.llamar_backend")
    def test_logout_limpia_sesion(self, mock_backend):
        mock_backend.return_value = ({"mensaje": "Sesión cerrada"}, 200)
        self.establecer_sesion()
        response = self.post("/logout")
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as sesion:
            self.assertNotIn("backend_token", sesion)


class TestComprasRoutes(BaseTestCase):
    """Pruebas para las rutas de Compras y Selección de Butacas."""

    @patch("frontend.utils.auth_helpers.llamar_backend")
    def test_ver_butacas_requiere_autenticacion(self, mock_backend):
        mock_backend.return_value = (None, 401)
        response = self.client.get("/butacas/10")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    @patch("frontend.utils.auth_helpers.llamar_backend")
    @patch("frontend.routes.compras_routes.llamar_backend")
    def test_ver_butacas_autenticado_200(self, mock_backend_compras, mock_backend_auth):
        mock_backend_auth.return_value = (self.usuario_cliente, 200)
        mock_backend_compras.side_effect = [
            ({"butacas": [{"id_butaca": 1, "fila": "A", "numero": 1}]}, 200),
            ({"cartelera": [{"id_funcion": 10, "fecha_hora_inicio": "Fri, 20 Nov 2026 20:00:00 GMT"}]}, 200)
        ]
        self.establecer_sesion()
        response = self.client.get("/butacas/10")
        self.assertEqual(response.status_code, 200)

    @patch("frontend.routes.compras_routes.llamar_backend")
    def test_ver_servicios_catalogo_publico(self, mock_backend):
        mock_backend.return_value = (
            {"servicios": [{"id_servicio": 1, "nombre": "Pochoclos Grandes", "precio": 3000}]},
            200
        )
        response = self.client.get("/servicios")
        self.assertEqual(response.status_code, 200)

    @patch("frontend.utils.auth_helpers.llamar_backend")
    @patch("frontend.routes.compras_routes.llamar_backend")
    def test_reservar_compra_nueva(self, mock_backend_compras, mock_backend_auth):
        mock_backend_auth.return_value = (self.usuario_cliente, 200)
        mock_backend_compras.return_value = (
            {"id_compra": 99, "fecha_hora_vencimiento": "2026-11-20 21:00:00"},
            201
        )
        self.establecer_sesion()
        response = self.post("/reservar-compra", data={
            "id_funcion": "10",
            "butacas": "1,2",
            "combos": "{}"
        })
        self.assertEqual(response.status_code, 302)


class TestUsuarioRoutes(BaseTestCase):
    """Pruebas para las rutas de Usuario (Historial y Comprobantes)."""

    @patch("frontend.utils.auth_helpers.llamar_backend")
    @patch("frontend.routes.usuario_routes.llamar_backend")
    def test_mis_compras_listado(self, mock_backend_usuario, mock_backend_auth):
        mock_backend_auth.return_value = (self.usuario_cliente, 200)
        mock_backend_usuario.side_effect = [
            ({"compras": [{"id_compra": 1, "estado": "confirmada", "total": 5000}]}, 200),
            ({"entradas": []}, 200)
        ]
        self.establecer_sesion()
        response = self.client.get("/mis-compras")
        self.assertEqual(response.status_code, 200)

    @patch("frontend.utils.auth_helpers.llamar_backend")
    @patch("frontend.routes.usuario_routes.llamar_backend")
    def test_descargar_comprobante_pdf_exitoso(self, mock_backend_usuario, mock_backend_auth):
        mock_backend_auth.return_value = (self.usuario_cliente, 200)
        mock_backend_usuario.return_value = (
            {
                "compra": {
                    "id_compra": 1,
                    "nombre": "Cliente",
                    "apellido": "Test",
                    "email": "cliente@example.com",
                    "estado": "aprobada",
                    "monto_total": 5000,
                    "total": 5000,
                    "fecha_hora": "2026-11-20 20:00:00"
                },
                "entradas": [],
                "servicios": []
            },
            200
        )
        self.establecer_sesion()
        response = self.client.get("/compras/1/comprobante/pdf")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/pdf")

    @patch("frontend.utils.auth_helpers.llamar_backend")
    @patch("frontend.routes.usuario_routes.llamar_backend")
    def test_descargar_comprobante_pdf_403_si_pendiente(self, mock_backend_usuario, mock_backend_auth):
        mock_backend_auth.return_value = (self.usuario_cliente, 200)
        mock_backend_usuario.return_value = (
            {
                "compra": {"id_compra": 1, "estado": "pendiente"},
                "entradas": [],
                "servicios": []
            },
            200
        )
        self.establecer_sesion()
        response = self.client.get("/compras/1/comprobante/pdf")
        self.assertEqual(response.status_code, 403)


class TestAdminRoutes(BaseTestCase):
    """Pruebas para las rutas de Administración."""

    @patch("frontend.utils.auth_helpers.llamar_backend")
    def test_admin_resumen_bloquea_cliente(self, mock_backend):
        mock_backend.return_value = (self.usuario_cliente, 200)
        self.establecer_sesion()
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 403)

    @patch("frontend.utils.auth_helpers.llamar_backend")
    @patch("frontend.routes.admin_routes.llamar_backend")
    def test_admin_resumen_acceso_permitido(self, mock_backend_admin, mock_backend_auth):
        mock_backend_auth.return_value = (self.usuario_admin, 200)
        mock_backend_admin.side_effect = [
            ({"resumen": {"total_ventas": 150000}}, 200),
            ({"ocupacion": []}, 200),
            ({"locales": []}, 200)
        ]
        self.establecer_sesion()
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 200)

    @patch("frontend.utils.auth_helpers.llamar_backend")
    @patch("frontend.routes.admin_routes.llamar_backend")
    def test_validar_qr_post(self, mock_backend_admin, mock_backend_auth):
        mock_backend_auth.return_value = (self.usuario_admin, 200)
        mock_backend_admin.return_value = ({"valido": True, "mensaje": "Entrada válida"}, 200)
        self.establecer_sesion()
        response = self.post("/admin/validar-qr", data={"codigo_qr": "QR123456"})
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()