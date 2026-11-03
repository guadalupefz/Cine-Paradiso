import os
import unittest
from urllib.parse import urlsplit, parse_qs
from unittest.mock import patch

os.environ.setdefault("SECRET_KEY", "clave-ficticia-para-pruebas-de-frontend-2026")
from frontend import app as frontend


class ContinuidadAcceso(unittest.TestCase):
    def setUp(self):
        frontend.app.config.update(TESTING=True)
        self.client=frontend.app.test_client()
        self.usuario={"id_usuario":8,"nombre":"Cliente","rol":"cliente"}
        self.login=({"access_token":"token-nuevo","usuario":self.usuario},200)
        self.llamadas=[]
        with self.client.session_transaction() as sesion:sesion['csrf_token']='csrf-inicial'
        parche=patch.object(frontend,'llamar_backend',side_effect=self.backend)
        parche.start()
        self.addCleanup(parche.stop)

    def backend(self,metodo,ruta,**datos):
        self.llamadas.append((metodo,ruta,datos))
        if ruta=='/auth/login':return self.login
        if ruta=='/usuarios/me':return self.usuario,200
        return [],200

    def post_login(self,**datos):
        with self.client.session_transaction() as sesion:csrf=sesion['csrf_token']
        return self.client.post('/login',data={'csrf_token':csrf,'email':'cliente@example.com','password':'ClavePrueba2026!',**datos})

    def test_butacas_exige_sesion_y_conserva_funcion_pelicula(self):
        respuesta=self.client.get('/butacas/15?id_pelicula=3')
        self.assertEqual(respuesta.status_code,302)
        destino=parse_qs(urlsplit(respuesta.location).query)['next'][0]
        self.assertEqual(destino,'/butacas/15?id_pelicula=3')
        self.assertFalse(any('/butacas' in ruta for _,ruta,_ in self.llamadas))

    def test_resumen_directo_exige_sesion_y_conserva_seleccion(self):
        respuesta=self.client.get('/compra?id_funcion=15&butacas=A1%2CA2')
        self.assertEqual(respuesta.status_code,302)
        destino=parse_qs(urlsplit(respuesta.location).query)['next'][0]
        self.assertEqual(urlsplit(destino).path,'/compra')
        self.assertEqual(parse_qs(urlsplit(destino).query),{'id_funcion':['15'],'butacas':['A1,A2']})

    def test_login_recupera_destino_guardado_y_rota_sesion(self):
        self.client.get('/compra?id_funcion=15&butacas=A1%2CA2')
        respuesta=self.post_login()
        self.assertEqual(urlsplit(respuesta.location).path,'/compra')
        self.assertEqual(parse_qs(urlsplit(respuesta.location).query)['butacas'],['A1,A2'])
        with self.client.session_transaction() as sesion:
            self.assertEqual(sesion['backend_token'],'token-nuevo')
            self.assertNotEqual(sesion['csrf_token'],'csrf-inicial')
            self.assertNotIn('destino_acceso',sesion)
            self.assertNotIn('password',sesion)

    def test_login_fallido_conserva_destino_sin_crear_sesion(self):
        self.login=({'error':'Credenciales inválidas'},401)
        respuesta=self.post_login(next='/butacas/15?id_pelicula=3')
        self.assertIn('/butacas/15?id_pelicula=3',respuesta.text)
        self.assertNotIn('value="ClavePrueba2026!"',respuesta.text)
        with self.client.session_transaction() as sesion:
            self.assertEqual(sesion['destino_acceso'],'/butacas/15?id_pelicula=3')
            self.assertNotIn('backend_token',sesion)

    def test_destinos_externos_y_rutas_no_permitidas_se_descartan(self):
        ataques=['https://evil.example','//evil.example','///evil.example','/\\evil.example',
                 '/%2f%2fevil.example','/%5cevil.example','/login','/registro','/logout',
                 '/butacas/15#externo','/butacas/15\r\nLocation:evil','/ruta-inexistente',
                 '/butacas/0','/compra?id_funcion=abc&butacas=1','/butacas/15?id_pelicula=1.5']
        for ataque in ataques:
            with self.subTest(ataque=ataque):
                respuesta=self.post_login(next=ataque)
                self.assertEqual(respuesta.location,'/')

    def test_destino_permitido_se_reconstruye_sin_parametros_extra(self):
        respuesta=self.post_login(next='/butacas/15?id_pelicula=3&next=//evil.example')
        self.assertEqual(respuesta.location,'/butacas/15?id_pelicula=3')

    def test_cliente_no_adquiere_permisos_por_destino_admin(self):
        respuesta=self.post_login(next='/admin')
        self.assertEqual(respuesta.location,'/admin')
        self.assertEqual(self.client.get(respuesta.location).status_code,403)

    def test_sin_destino_administrador_va_al_panel(self):
        self.usuario['rol']='administrador'
        respuesta=self.post_login()
        self.assertEqual(respuesta.location,'/admin')

    def test_compra_con_sesion_sigue_mostrando_resumen_preliminar(self):
        self.post_login()
        respuesta=self.client.get('/compra?id_funcion=15&butacas=A1%2CA2')
        self.assertEqual(respuesta.status_code,200)
        self.assertIn('A1',respuesta.text)
        self.assertIn('La compra todavía no está',respuesta.text)

    def test_login_sin_csrf_no_llama_a_la_api(self):
        respuesta=self.client.post('/login',data={'email':'cliente@example.com','password':'ClavePrueba2026!'})
        self.assertEqual(respuesta.status_code,400)
        self.assertFalse(any(ruta=='/auth/login' for _,ruta,_ in self.llamadas))


if __name__=='__main__':unittest.main()
