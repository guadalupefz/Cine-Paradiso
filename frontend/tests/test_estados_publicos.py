import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SECRET_KEY", "clave-ficticia-para-pruebas-de-frontend-2026")
from frontend import app as frontend


class EstadosPublicos(unittest.TestCase):
    def setUp(self):
        frontend.app.config.update(TESTING=True)
        self.client=frontend.app.test_client()
        self.usuario={"id_usuario":8,"nombre":"Persona de prueba","rol":"cliente"}
        self.errores={}
        self.llamadas=[]
        self.compras=[{"id_compra":17,"fecha_hora":"2026-11-03","estado":"confirmada","total":"8000.00"}]
        parche=patch.object(frontend,"llamar_backend",side_effect=self.backend)
        parche.start()
        self.addCleanup(parche.stop)

    def backend(self,metodo,ruta,**argumentos):
        self.llamadas.append((metodo,ruta,argumentos))
        if ruta in self.errores:return {"error":"No disponible"},503
        if ruta=="/usuarios/me":return self.usuario,200
        if ruta=="/compras":return self.compras,200
        if ruta=="/compras/17/entradas":return [],200
        if ruta=="/auth/logout":return {"mensaje":"Sesión cerrada"},200
        return [],200

    def iniciar_sesion(self):
        with self.client.session_transaction() as sesion:
            sesion.update(backend_token="token-ficticio",csrf_token="csrf-ficticio")

    def test_error_cartelera_no_anuncia_catalogo_vacio(self):
        self.errores["/peliculas"]=503
        respuesta=self.client.get("/")
        self.assertIn("No pudimos cargar la cartelera",respuesta.text)
        self.assertNotIn("No hay películas disponibles en este momento.",respuesta.text)

    def test_catalogo_vacio_no_anuncia_fallo(self):
        respuesta=self.client.get("/")
        self.assertIn("No hay películas disponibles en este momento.",respuesta.text)
        self.assertNotIn("No pudimos cargar la cartelera",respuesta.text)

    def test_error_compras_no_anuncia_historial_vacio(self):
        self.iniciar_sesion()
        self.errores["/compras"]=503
        respuesta=self.client.get("/mis-compras")
        self.assertIn("No se pudieron cargar tus compras",respuesta.text)
        self.assertNotIn("No tenés compras registradas.",respuesta.text)
        self.assertFalse(any(ruta.endswith('/entradas') for _,ruta,_ in self.llamadas))

    def test_error_entradas_conserva_compra_y_comprobante(self):
        self.iniciar_sesion()
        self.errores["/compras/17/entradas"]=503
        respuesta=self.client.get("/mis-compras")
        self.assertIn("Compra 17",respuesta.text)
        self.assertIn("No se pudieron cargar las entradas de esta compra.",respuesta.text)
        self.assertIn('/compras/17/comprobante',respuesta.text)

    def test_menu_admin_depende_del_usuario_verificado(self):
        self.iniciar_sesion()
        cliente=self.client.get("/")
        self.assertNotIn('href="/admin"',cliente.text)
        self.usuario['rol']=' Administrador '
        administrador=self.client.get("/")
        self.assertIn('href="/admin"',administrador.text)

    def test_logout_del_menu_conserva_csrf(self):
        self.iniciar_sesion()
        rechazada=self.client.post('/logout')
        self.assertEqual(rechazada.status_code,400)
        self.assertFalse(any(ruta=='/auth/logout' for _,ruta,_ in self.llamadas))
        valida=self.client.post('/logout',data={'csrf_token':'csrf-ficticio'})
        self.assertEqual(valida.status_code,302)
        self.assertIn(('POST','/auth/logout',{}),self.llamadas)
        with self.client.session_transaction() as sesion:
            self.assertNotIn('backend_token',sesion)

    def test_pagina_inexistente_conserva_base_y_estado_404(self):
        respuesta=self.client.get('/pagina-que-no-existe')
        self.assertEqual(respuesta.status_code,404)
        self.assertIn("La página que buscás no está disponible",respuesta.text)
        self.assertIn('id="contenido-principal"',respuesta.text)


if __name__=='__main__':
    unittest.main()
