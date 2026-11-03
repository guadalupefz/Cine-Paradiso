import os
import unittest
from datetime import datetime,timedelta
from unittest.mock import MagicMock,patch

os.environ.setdefault("SECRET_KEY", "clave-ficticia-para-pruebas-backend-2026")
from backend.src.services import reservas_service as reservas


class InicioFuncionReserva(unittest.TestCase):
    def setUp(self):
        self.ahora=datetime(2026,11,3,18,0,0)
        self.conexion=MagicMock()
        self.parche('get_connection',return_value=self.conexion)
        self.funcion=self.parche('obtener_funcion',return_value={'id_funcion':15,'precio_base':'8000.00','fecha_hora_inicio':self.ahora+timedelta(hours=1)})
        self.reloj=self.parche('obtener_hora_actual',return_value=self.ahora)
        self.parche('obtener_butacas_de_funcion',return_value=[{'id_butaca':11}])
        self.parche('obtener_butacas_ocupadas_con_bloqueo',return_value=[])
        self.servicio=self.parche('obtener_servicio',return_value={'id_servicio':3,'precio':'3000.00'})
        self.limpiar=self.parche('limpiar_reservas_expiradas')
        self.crear=self.parche('crear_compra_pendiente',return_value=17)
        self.entradas=self.parche('crear_entradas_reserva')
        self.adicional=self.parche('agregar_servicio_a_compra')

    def parche(self,nombre,**argumentos):
        parche=patch.object(reservas,nombre,**argumentos)
        valor=parche.start()
        self.addCleanup(parche.stop)
        return valor

    def test_pasada_rechaza_antes_de_cualquier_escritura(self):
        self.funcion.return_value['fecha_hora_inicio']=self.ahora-timedelta(seconds=1)
        reserva,error=reservas.crear_reserva(8,15,[11],[{'id_servicio':3,'cantidad':1}])
        self.assertIsNone(reserva)
        self.assertEqual(error['status_code'],400)
        self.assertEqual(error['error'],'FUNCION_INICIADA')
        for operacion in (self.limpiar,self.crear,self.entradas,self.adicional,self.servicio):operacion.assert_not_called()
        self.conexion.commit.assert_not_called()
        self.conexion.rollback.assert_called_once()
        self.conexion.close.assert_called_once()

    def test_inicio_exacto_tampoco_crea_reserva(self):
        self.funcion.return_value['fecha_hora_inicio']=self.ahora
        reserva,error=reservas.crear_reserva(8,15,[11])
        self.assertIsNone(reserva)
        self.assertEqual(error['status_code'],400)
        self.crear.assert_not_called()

    def test_reloj_posterior_al_inicio_rechaza_aunque_el_pedido_arranco_antes(self):
        self.funcion.return_value['fecha_hora_inicio']=self.ahora+timedelta(seconds=2)
        self.reloj.return_value=self.ahora+timedelta(seconds=3)
        reserva,error=reservas.crear_reserva(8,15,[11])
        self.assertIsNone(reserva)
        self.assertEqual(error['status_code'],400)
        self.crear.assert_not_called()

    def test_futura_conserva_servicios_y_precio_historico(self):
        reserva,error=reservas.crear_reserva(8,15,[11],[{'id_servicio':3,'cantidad':1}])
        self.assertIsNone(error)
        self.assertEqual(reserva['estado'],'pendiente')
        self.assertEqual(reserva['total'],11000.0)
        self.assertEqual(str(reserva['servicios'][0]['precio_unitario']),'3000.00')
        self.crear.assert_called_once()
        self.adicional.assert_called_once()
        self.conexion.commit.assert_called_once()

    def test_funcion_inexistente_conserva_404(self):
        self.funcion.return_value=None
        reserva,error=reservas.crear_reserva(8,15,[11])
        self.assertIsNone(reserva)
        self.assertEqual(error['status_code'],404)
        self.crear.assert_not_called()
        self.reloj.assert_not_called()


if __name__=='__main__':unittest.main()
