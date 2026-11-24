import unittest
from unittest.mock import MagicMock, patch

from flask import Flask

from backend.src.services import correo_service


class TestCorreoService(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            MAIL_DEFAULT_SENDER="cineparadiso@example.com",
            FRONTEND_URL="http://127.0.0.1:8080"
        )
        correo_service.mail.init_app(self.app)
        self.comprobante = {
            "compra": {
                "id_compra": 17,
                "id_usuario": 8,
                "nombre": "Cliente de prueba",
                "email": "cliente@example.com",
                "total": "8000.00",
                "estado": "confirmada"
            },
            "entradas": [
                {
                    "id_entrada": 19,
                    "pelicula": "El secreto de sus ojos",
                    "fecha_hora_inicio": "2026-11-10 20:00:00",
                    "local": "Cine Paradiso Caballito",
                    "direccion": "Av. Rivadavia 1234, Buenos Aires",
                    "sala": "Sala 1",
                    "fila": "A",
                    "numero": 7
                }
            ],
            "servicios": []
        }

        self.entradas_qr = [
            {
                "id_entrada": 19,
                "qr_token": "token-prueba-123"
            }
        ]

    def test_enviar_correo_con_detalle_enlaces_y_qr(self):
        imagen = MagicMock()
        imagen.save.side_effect = lambda archivo, format: archivo.write(b"imagen-qr")

        with self.app.app_context():
            with patch.object(
                correo_service,
                "generar_qr",
                return_value=imagen
            ) as generar_qr, patch.object(
                correo_service.mail,
                "send"
            ) as enviar:

                correo_service.enviar_mail_compra(
                    self.comprobante,
                    self.entradas_qr
                )

        generar_qr.assert_called_once_with("token-prueba-123")
        enviar.assert_called_once()

        mensaje = enviar.call_args.args[0]

        self.assertEqual(
            mensaje.recipients,
            ["cliente@example.com"]
        )

        self.assertIn("El secreto de sus ojos", mensaje.body)
        self.assertIn("Cine Paradiso Caballito", mensaje.body)
        self.assertIn("Av. Rivadavia 1234", mensaje.body)
        self.assertIn("Sala 1", mensaje.body)
        self.assertIn("A7", mensaje.body)
        self.assertIn("https://www.google.com/maps/search/", mensaje.body)
        self.assertIn("http://127.0.0.1:8080/mis-compras", mensaje.body)

        self.assertEqual(len(mensaje.attachments), 1)
        self.assertEqual(
            mensaje.attachments[0].filename,
            "entrada_19.png"
        )

    def test_no_envia_correo_si_compra_no_esta_confirmada(self):
        self.comprobante["compra"]["estado"] = "pendiente"

        with self.app.app_context():
            with patch.object(correo_service.mail, "send") as enviar:
                with self.assertRaisesRegex(
                    ValueError,
                    "La compra no está confirmada"
                ):
                    correo_service.enviar_mail_compra(
                        self.comprobante,
                        self.entradas_qr
                    )

        enviar.assert_not_called()


if __name__ == "__main__":
    unittest.main()