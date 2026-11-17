import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

os.environ.setdefault("SECRET_KEY", "clave-ficticia-para-pruebas-backend-2026")
from backend.src.services import compra_service as compras
from backend.src.validators.inicio_funcion_validator import validar_inicio_funcion


class InicioFuncionCompra(unittest.TestCase):
    def setUp(self):
        self.ahora = datetime(2026, 11, 3, 18, 0, 0)
        self.cursor = MagicMock()
        self.parche("obtener_hora_actual", return_value=self.ahora)
        self.parche("obtener_usuario", return_value={"id_usuario": 8})
        self.funcion = self.parche("obtener_funcion", return_value={
            "id_funcion": 15,
            "id_sala": 3,
            "precio_base": "8000.00",
            "fecha_hora_inicio": self.ahora + timedelta(hours=1)
        })
        self.inicio_compra = self.parche("obtener_inicio_funciones_compra", return_value=self.ahora + timedelta(hours=1))
        self.parche("obtener_butacas_de_funcion", return_value=[{"id_butaca": 11}])
        self.parche("obtener_butacas_ocupadas", return_value=[])
        self.limpiar = self.parche("limpiar_reservas_expiradas")
        self.crear_compra = self.parche("crear_compra", return_value=17)
        self.crear_entrada = self.parche("crear_entrada", return_value=19)
        self.entradas = self.parche("obtener_entradas_por_compra", return_value=[
            {"id_entrada": 19, "id_funcion": 15, "id_butaca": 11}
        ])
        self.compra = self.parche("obtener_compra_para_confirmar", return_value={
            "id_compra": 17,
            "id_usuario": 8,
            "total": "8000.00",
            "estado": "pendiente",
            "vigente": True
        })
        self.actualizar_estado = self.parche("actualizar_estado_compra", return_value=1)
        self.liberar_entradas = self.parche("liberar_entradas_compra")
        self.actualizar_qr = self.parche("actualizar_qr_entrada")
        self.correo = self.parche("enviar_mail_compra")

    def parche(self, nombre, **argumentos):
        parche = patch.object(compras, nombre, **argumentos)
        valor = parche.start()
        self.addCleanup(parche.stop)
        return valor

    def test_limite_inicio_se_rechaza_e_inicio_posterior_se_acepta(self):
        for fecha in (self.ahora - timedelta(seconds=1), self.ahora):
            with self.subTest(fecha=fecha), self.assertRaisesRegex(ValueError, "ya comenzó"):
                validar_inicio_funcion(fecha, self.ahora)
        validar_inicio_funcion(self.ahora + timedelta(seconds=1), self.ahora)

    def test_horario_ausente_no_se_acepta(self):
        with self.assertRaises(ValueError):
            validar_inicio_funcion(None, self.ahora)

    def test_compra_pasada_rechaza_antes_de_cualquier_escritura(self):
        self.funcion.return_value["fecha_hora_inicio"] = self.ahora - timedelta(seconds=1)
        resultado, errores = compras.realizar_compra(self.cursor, 8, 15, [11])
        self.assertIsNone(resultado)
        self.assertEqual(errores[0]["code"], "FUNCION_NO_DISPONIBLE")
        self.limpiar.assert_not_called()
        self.crear_compra.assert_not_called()
        self.crear_entrada.assert_not_called()

    def test_compra_en_inicio_exacto_no_inserta(self):
        self.funcion.return_value["fecha_hora_inicio"] = self.ahora
        resultado, errores = compras.realizar_compra(self.cursor, 8, 15, [11])
        self.assertIsNone(resultado)
        self.assertEqual(errores[0]["code"], "FUNCION_NO_DISPONIBLE")
        self.crear_compra.assert_not_called()
        self.crear_entrada.assert_not_called()

    def test_compra_futura_conserva_total_y_entradas(self):
        resultado, errores = compras.realizar_compra(self.cursor, 8, 15, [11])
        self.assertIsNone(errores)
        self.assertEqual(resultado["id_compra"], 17)
        self.assertEqual(resultado["total"], "8000.00")
        self.assertEqual(resultado["estado"], "confirmada")
        self.assertEqual(resultado["entradas"][0]["id_butaca"], 11)
        self.assertIn("qr_token", resultado["entradas"][0])
        self.limpiar.assert_called_once()
        self.crear_compra.assert_called_once()
        self.crear_entrada.assert_called_once()

    def test_confirmar_reserva_de_funcion_iniciada_no_cambia_estado_ni_qr(self):
        self.inicio_compra.return_value = self.ahora - timedelta(seconds=1)
        resultado, errores = compras.confirmar_compra(self.cursor, 8, 17)
        self.assertIsNone(resultado)
        self.assertEqual(errores[0]["code"], "FUNCION_NO_DISPONIBLE")
        self.actualizar_estado.assert_not_called()
        self.actualizar_qr.assert_not_called()

    def test_confirmacion_futura_conserva_resultado(self):
        resultado, errores = compras.confirmar_compra(self.cursor, 8, 17)
        self.assertIsNone(errores)
        self.assertEqual(resultado["id_compra"], 17)
        self.assertEqual(resultado["estado"], "confirmada")
        self.assertEqual(resultado["total"], "8000.00")
        self.assertEqual(resultado["entradas"][0]["id_entrada"], 19)
        self.actualizar_estado.assert_called_once()
        self.actualizar_qr.assert_called_once()

    def test_reserva_vencida_se_expira_y_libera_entradas(self):
        self.compra.return_value["vigente"] = False
        resultado, errores = compras.confirmar_compra(self.cursor, 8, 17)
        self.assertIsNone(errores)
        self.assertTrue(resultado["reserva_vencida"])
        self.actualizar_estado.assert_called_once()
        self.liberar_entradas.assert_called_once_with(self.cursor, 17)
        self.actualizar_qr.assert_not_called()

    def test_compra_no_pertenece_al_usuario(self):
        self.compra.return_value["id_usuario"] = 9
        resultado, errores = compras.confirmar_compra(self.cursor, 8, 17)
        self.assertIsNone(resultado)
        self.assertEqual(errores[0]["code"], "COMPRA_NO_AUTORIZADA")
        self.actualizar_estado.assert_not_called()
        self.actualizar_qr.assert_not_called()

    def test_enviar_comprobante_correctamente(self):
        comprobante = {"compra": {"id_compra": 17}}
        entradas = [{"id_entrada": 19, "qr_token": "token-prueba"}]

        resultado = compras.enviar_comprobante_compra(
            comprobante, entradas
        )

        self.assertTrue(resultado["correo_enviado"])
        self.correo.assert_called_once_with(comprobante, entradas)

    def test_compra_no_se_ve_afectada_por_error_de_correo(self):
        self.correo.side_effect = RuntimeError("Error SMTP")
        resultado = compras.enviar_comprobante_compra(
            {"compra": {"id_compra": 17}}, [{"id_entrada": 19}]
        )
        self.assertFalse(resultado["correo_enviado"])
        self.assertIn("no se pudo enviar el correo", resultado["mensaje_correo"])


if __name__ == "__main__":
    unittest.main()