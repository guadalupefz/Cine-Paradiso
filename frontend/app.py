import os
import secrets
from functools import wraps
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for, flash, g, abort

from flask import Response

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:5001/api").rstrip("/")
BACKEND_ORIGEN = BACKEND_URL.rsplit("/api", 1)[0]
app = Flask(__name__, template_folder=str(Path(__file__).resolve().parent / "templates"), static_folder=str(Path(__file__).resolve().parent / "static"))
app.config.update(
    SECRET_KEY=os.environ.get("FRONTEND_SECRET_KEY") or os.environ["SECRET_KEY"] + ":frontend",
    SESSION_COOKIE_NAME="cine_frontend",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    MAX_CONTENT_LENGTH=1024 * 1024,
)

def llamar_backend(metodo, ruta, **argumentos):
    cookies = {}
    if session.get("backend_cookie"):
        cookies["cine_backend"] = session["backend_cookie"]
    try:
        respuesta = requests.request(metodo, BACKEND_URL + ruta, cookies=cookies, timeout=15, **argumentos)
        nueva_cookie = respuesta.cookies.get("cine_backend")
        if nueva_cookie:
            session["backend_cookie"] = nueva_cookie
        try:
            datos = respuesta.json()
        except ValueError:
            datos = {"error": "El backend devolvió una respuesta no válida."}
        return datos, respuesta.status_code
    except requests.RequestException:
        return {"error": "No se pudo conectar con el servidor. Intentá nuevamente."}, 503

def mensaje_error(datos):
    if isinstance(datos, dict):
        errores = datos.get("errors")
        if errores:
            return "; ".join(e.get("message", "Datos inválidos") for e in errores)
        return datos.get("mensaje") or datos.get("message") or datos.get("error") or "No se pudo completar la operación."
    return "No se pudo completar la operación."

def lista(datos, clave):
    return datos if isinstance(datos, list) else datos.get(clave, []) if isinstance(datos, dict) else []

def usuario_actual():
    if not hasattr(g, "usuario"):
        g.usuario = None
        if session.get("backend_cookie"):
            datos, estado = llamar_backend("GET", "/usuarios/me")
            if estado == 200:
                g.usuario = datos
            elif estado in (401, 403):
                session.pop("backend_cookie", None)
    return g.usuario

def requiere_usuario(funcion):
    @wraps(funcion)
    def vista(*args, **kwargs):
        if usuario_actual() is None:
            flash("Iniciá sesión para continuar.", "error")
            return redirect(url_for("login"))
        return funcion(*args, **kwargs)
    return vista

def requiere_admin(funcion):
    @wraps(funcion)
    @requiere_usuario
    def vista(*args, **kwargs):
        if usuario_actual().get("rol", "").strip().casefold() != "administrador":
            abort(403)
        return funcion(*args, **kwargs)
    return vista

@app.before_request
def verificar_formularios():
    if request.method == "POST":
        recibido = request.form.get("csrf_token", "")
        esperado = session.get("csrf_token", "")
        if not esperado or not secrets.compare_digest(recibido, esperado):
            abort(400, "El formulario venció. Volvé a cargar la página.")

@app.context_processor
def datos_comunes():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(24)
    return {"usuario_actual": usuario_actual(), "csrf_token": session["csrf_token"]}

@app.errorhandler(403)
def acceso_denegado(error):
    return render_template("error.html", mensaje="No tenés permisos para acceder a esta sección."), 403

@app.errorhandler(400)
def formulario_invalido(error):
    return render_template("error.html", mensaje=getattr(error, "description", "Formulario inválido")), 400

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        datos, estado = llamar_backend("POST", "/auth/login", json={"email": request.form.get("email", ""), "password": request.form.get("password", "")})
        if estado == 200:
            flash("Sesión iniciada.", "ok")
            usuario = datos.get("usuario", {})
            return redirect(url_for("admin_resumen" if usuario.get("rol", "").casefold() == "administrador" else "index"))
        flash(mensaje_error(datos), "error")
    return render_template("login.html")

@app.post("/logout")
def logout():
    llamar_backend("POST", "/auth/logout")
    session.clear()
    return redirect(url_for("index"))

@app.get("/")
def index():
    datos, estado = llamar_backend("GET", "/cartelera")
    peliculas, vistos = [], set()
    for peli in lista(datos, "cartelera"):
        if peli["id_pelicula"] not in vistos:
            peli["duracion"] = peli.get("duracion_minutos")
            poster = peli.get("poster", "")
            if poster and not poster.startswith(("http://", "https://")):
                peli["poster"] = urljoin(BACKEND_ORIGEN + "/", poster.lstrip("/"))
            peliculas.append(peli)
            vistos.add(peli["id_pelicula"])
    if estado != 200:
        flash(mensaje_error(datos), "error")
    return render_template("cartelera.html", peliculas=peliculas)

@app.get("/funciones")
def ver_funciones():
    id_pelicula = request.args.get("id_pelicula", type=int)
    datos, estado = llamar_backend("GET", "/funciones")
    funciones = [f for f in lista(datos, "funciones") if not id_pelicula or f.get("id_pelicula") == id_pelicula]
    for funcion in funciones:
        try:
            fecha = datetime.strptime(funcion["fecha_hora_inicio"], "%a, %d %b %Y %H:%M:%S GMT")
            funcion["fecha"], funcion["horario"] = fecha.strftime("%d/%m/%Y"), fecha.strftime("%H:%M")
        except (ValueError, TypeError):
            funcion["fecha"], funcion["horario"] = funcion.get("fecha_hora_inicio", ""), ""
    pelicula = {"titulo": funciones[0]["titulo"] if funciones else "Funciones"}
    return render_template("funciones.html", funciones=funciones, pelicula=pelicula, id_pelicula=id_pelicula, error=estado != 200)

@app.get("/butacas/<int:id_funcion>")
@requiere_usuario
def ver_butacas(id_funcion):
    datos, estado = llamar_backend("GET", f"/funciones/{id_funcion}/butacas")
    return render_template("butacas.html", butacas=lista(datos,"butacas"), pelicula={"titulo": "Selección de butacas"}, id_funcion=id_funcion, id_pelicula=request.args.get("id_pelicula",type=int), error=estado != 200)

@app.get("/compra")
def ver_compra():
    id_funcion = request.args.get("id_funcion",type=int)
    butacas = [b.strip() for b in request.args.get("butacas", "").split(",") if b.strip()]
    return render_template("compra.html", id_funcion=id_funcion, butacas=butacas, error=not id_funcion or not butacas)

@app.get("/servicios")
def ver_servicios():
    datos, estado = llamar_backend("GET", "/servicios")
    return render_template("servicios.html", servicios=lista(datos,"servicios"), error=estado != 200)

@app.get("/mis-compras")
@requiere_usuario
def mis_compras():
    datos, estado = llamar_backend("GET", "/compras")

    if estado != 200:
        flash(mensaje_error(datos), "error")

    compras = lista(datos, "compras")

    for compra in compras:
        
        entradas, estado_entradas = llamar_backend(
            "GET",
            f"/compras/{compra['id_compra']}/entradas"
        )

        compra["entradas"] = lista(entradas, "entradas") if estado_entradas == 200 else []

    return render_template("compras.html", compras=compras)


@app.get("/admin")
@requiere_admin
def admin_resumen():
    ventas, ev = llamar_backend("GET", "/estadisticas/ventas")
    ocupacion, eo = llamar_backend("GET", "/estadisticas/ocupacion")
    if ev != 200 or eo != 200:
        flash("No se pudieron cargar todas las estadísticas.", "error")
    return render_template("admin/resumen_admin.html", ventas=ventas, ocupacion=ocupacion)

@app.route("/admin/servicios", methods=["GET", "POST"])
@requiere_admin
def admin_servicios():
    if request.method == "POST":
        accion = request.form.get("accion", "crear")
        identificador = request.form.get("id_servicio", type=int)
        if accion not in ("crear", "editar", "eliminar") or (accion != "crear" and not identificador):
            abort(400)
        metodo = {"crear":"POST", "editar":"PUT", "eliminar":"DELETE"}[accion]
        ruta = "/servicios" + (f"/{identificador}" if accion != "crear" else "")
        argumentos = {} if accion == "eliminar" else {"json":{"nombre":request.form.get("nombre", ""),"precio":request.form.get("precio", "")}}
        datos, estado = llamar_backend(metodo, ruta, **argumentos)
        flash(mensaje_error(datos), "ok" if estado in (200,201) else "error")
        return redirect(url_for("admin_servicios"))
    datos, estado = llamar_backend("GET", "/servicios")
    servicios = lista(datos, "servicios")
    editar = request.args.get("editar", type=int)
    servicio_editar = next((s for s in servicios if s["id_servicio"] == editar), None)
    if estado != 200:
        flash(mensaje_error(datos), "error")
    return render_template("admin/servicios_admin.html", servicios=servicios, servicio_editar=servicio_editar)

@app.route("/admin/peliculas", methods=["GET", "POST"])
@requiere_admin
def admin_peliculas():
    resultado_api = None
    if request.method == "POST":
        accion = request.form.get("accion", "crear")
        if accion in ("buscar", "importar"):
            resultado_api, estado = llamar_backend("GET" if accion == "buscar" else "POST", "/pelicula", params={"titulo":request.form.get("titulo", "")})
            if estado != 200 or accion == "importar":
                flash(mensaje_error(resultado_api), "ok" if estado == 200 else "error")
            if accion == "importar":
                return redirect(url_for("admin_peliculas"))
        elif accion in ("crear", "editar"):
            identificador = request.form.get("id_pelicula",type=int)
            datos = {k:request.form.get(k, "") for k in ("titulo","sinopsis","poster","clasificacion","genero")}
            datos["duracion_minutos"] = request.form.get("duracion_minutos",type=int)
            ruta = "/peliculas" + (f"/{identificador}" if accion == "editar" and identificador else "")
            resultado, estado = llamar_backend("PUT" if accion == "editar" else "POST", ruta, json=datos)
            flash(mensaje_error(resultado), "ok" if estado in (200,201) else "error")
            return redirect(url_for("admin_peliculas"))
        else:
            abort(400)
    datos, estado = llamar_backend("GET", "/peliculas")
    peliculas = lista(datos,"peliculas")
    editar = request.args.get("editar", type=int)
    pelicula_editar = next((p for p in peliculas if p["id_pelicula"] == editar), None)
    if estado != 200:
        flash(mensaje_error(datos), "error")
    return render_template("admin/peliculas_admin.html", peliculas=peliculas, pelicula_editar=pelicula_editar, resultado_api=resultado_api)

@app.route("/admin/funciones", methods=["GET", "POST"])
@requiere_admin
def admin_funciones():
    if request.method == "POST":
        identificador = request.form.get("id_funcion",type=int)
        datos = {"id_pelicula":request.form.get("id_pelicula",type=int), "id_sala":request.form.get("id_sala",type=int), "fecha_hora_inicio":request.form.get("fecha_hora_inicio", ""), "precio_base":request.form.get("precio_base", "")}
        resultado, estado = llamar_backend("PUT" if identificador else "POST", "/funciones" + (f"/{identificador}" if identificador else ""), json=datos)
        flash(mensaje_error(resultado), "ok" if estado in (200,201) else "error")
        return redirect(url_for("admin_funciones"))
    p, ep = llamar_backend("GET", "/peliculas")
    f, ef = llamar_backend("GET", "/funciones")
    l, el = llamar_backend("GET", "/locales")
    salas = []
    for local in lista(l,"locales"):
        datos, estado = llamar_backend("GET", f"/locales/{local['id_local']}/salas")
        for sala in lista(datos,"salas"):
            sala["local_nombre"] = local["nombre"]
            salas.append(sala)
    if any(e != 200 for e in (ep,ef,el)):
        flash("No se pudieron cargar todos los datos del formulario.", "error")
    funciones = lista(f,"funciones")
    editar = request.args.get("editar",type=int)
    funcion_editar = next((x for x in funciones if x["id_funcion"] == editar),None)
    if funcion_editar:
        try:
            funcion_editar["fecha_formulario"] = datetime.strptime(funcion_editar["fecha_hora_inicio"],"%a, %d %b %Y %H:%M:%S GMT").strftime("%Y-%m-%dT%H:%M")
        except (ValueError,TypeError):
            funcion_editar["fecha_formulario"] = ""
    return render_template("admin/funciones_admin.html", peliculas=lista(p,"peliculas"), funciones=funciones, salas=salas, funcion_editar=funcion_editar)

@app.route("/admin/validar-qr", methods=["GET", "POST"])
@requiere_admin
def validar_qr():
    resultado = None
    if request.method == "POST":
        resultado, estado = llamar_backend("POST", "/qr/validar", json={"qr_token":request.form.get("qr_token", ""),"id_funcion":request.form.get("id_funcion",type=int)})
        flash(mensaje_error(resultado),"ok" if estado == 200 else "error")
    return render_template("admin/validar_qr.html", resultado=resultado)


@app.get("/entradas/<int:id_entrada>/qr")
@requiere_usuario
def ver_qr_cliente(id_entrada):

    respuesta = requests.get(
        f"{BACKEND_URL}/qr/{id_entrada}",
        cookies={"cine_backend": session.get("backend_cookie", "")},
        timeout=10
    )

    if respuesta.status_code != 200:
        abort(respuesta.status_code)

    return Response(respuesta.content, mimetype="image/png")


if __name__ == "__main__":
    app.run("127.0.0.1",port=8080,debug=os.environ.get("FLASK_DEBUG") == "1")