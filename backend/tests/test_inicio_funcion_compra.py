import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

os.environ.setdefault("SECRET_KEY", "clave-ficticia-para-pruebas-backend-2026")
from backend.src.services import compra_service as compras
from backend.src.validators.inicio_funcion_validator import validar_inicio_funcion


class InicioFuncionCompra(unittest.TestCase):
    def setUp(self):
        self.ahora=datetime(2026,11,3,18,0,0)
        self.conexion=MagicMock()
        self.cursor=self.conexion.cursor.return_value
        self.cursor.fetchone.return_value={"id_compra":17,"id_usuario":8,"total":"8000.00","estado":"pendiente","vigente":True}
        self.cursor.rowcount=1
        self.parche('get_connection',return_value=self.conexion)
        self.parche('obtener_hora_actual',return_value=self.ahora)
        self.parche('obtener_usuario',return_value={'id_usuario':8})
        self.funcion=self.parche('obtener_funcion',return_value={'id_funcion':15,'id_sala':3,'precio_base':'8000.00','fecha_hora_inicio':self.ahora+timedelta(hours=1)})
        self.inicio_compra=self.parche('obtener_inicio_funciones_compra',return_value=self.ahora+timedelta(hours=1))
        self.parche('obtener_butacas_de_funcion',return_value=[{'id_butaca':11}])
        self.parche('obtener_butacas_ocupadas',return_value=[])
        self.limpiar=self.parche('limpiar_reservas_expiradas')
        self.crear_compra=self.parche('crear_compra',return_value=17)
        self.crear_entrada=self.parche('crear_entrada',return_value=19)
        self.parche('obtener_entradas_por_compra',return_value=[{'id_entrada':19,'id_funcion':15,'id_butaca':11}])
        self.parche('obtener_comprobante',return_value={})
        self.correo=self.parche('enviar_mail_compra')

    def parche(self,nombre,**argumentos):
        parche=patch.object(compras,nombre,**argumentos)
        valor=parche.start()
        self.addCleanup(parche.stop)
        return valor

    def test_limite_inicio_se_rechaza_e_inicio_posterior_se_acepta(self):
        for fecha in (self.ahora-timedelta(seconds=1),self.ahora):
            with self.subTest(fecha=fecha),self.assertRaisesRegex(ValueError,'ya comenzó'):
                validar_inicio_funcion(fecha,self.ahora)
        validar_inicio_funcion(self.ahora+timedelta(seconds=1),self.ahora)

    def test_horario_ausente_no_se_acepta(self):
        with self.assertRaises(ValueError):validar_inicio_funcion(None,self.ahora)

    def test_compra_pasada_rechaza_antes_de_cualquier_escritura(self):
        self.funcion.return_value['fecha_hora_inicio']=self.ahora-timedelta(seconds=1)
        with self.assertRaisesRegex(ValueError,'ya comenzó'):
            compras.realizar_compra(8,15,[11])
        self.limpiar.assert_not_called()
        self.crear_compra.assert_not_called()
        self.crear_entrada.assert_not_called()
        self.conexion.commit.assert_not_called()
        self.conexion.rollback.assert_called_once()
        self.conexion.close.assert_called_once()
        self.correo.assert_not_called()

    def test_compra_en_inicio_exacto_no_inserta(self):
        self.funcion.return_value['fecha_hora_inicio']=self.ahora
        with self.assertRaises(ValueError):compras.realizar_compra(8,15,[11])
        self.crear_compra.assert_not_called()
        self.crear_entrada.assert_not_called()

    def test_compra_futura_conserva_total_entradas_y_commit(self):
        resultado=compras.realizar_compra(8,15,[11])
        self.assertEqual(resultado['id_compra'],17)
        self.assertEqual(resultado['total'],'8000.00')
        self.assertEqual(resultado['entradas'][0]['id_butaca'],11)
        self.conexion.commit.assert_called_once()
        self.conexion.rollback.assert_not_called()

    def test_confirmar_reserva_de_funcion_iniciada_no_aprueba_ni_cambia_qr(self):
        self.inicio_compra.return_value=self.ahora-timedelta(seconds=1)
        with self.assertRaisesRegex(ValueError,'ya comenzó'):
            compras.confirmar_compra(8,17)
        self.assertFalse(any(llamada.args[0].lstrip().startswith('UPDATE') for llamada in self.cursor.execute.call_args_list))
        self.conexion.commit.assert_not_called()
        self.conexion.rollback.assert_called_once()
        self.correo.assert_not_called()

    def test_confirmacion_futura_conserva_resultado(self):
        resultado=compras.confirmar_compra(8,17)
        self.assertEqual(resultado['estado'], 'confirmada')
        self.assertEqual(resultado['entradas'][0]['id_entrada'],19)
        self.conexion.commit.assert_called_once()


if __name__=='__main__':unittest.main()
