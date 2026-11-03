import os
import secrets
from functools import wraps
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlsplit, unquote, parse_qs
from werkzeug.exceptions import HTTPException

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
    cabeceras = {}
    if session.get("backend_token"):
        cabeceras["Authorization"] = "Bearer " + session["backend_token"]
    try:
        respuesta = requests.request(metodo, BACKEND_URL + ruta, headers=cabeceras, timeout=15, **argumentos)
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
        if session.get("backend_token"):
            datos, estado = llamar_backend("GET", "/usuarios/me")
            if estado == 200:
                g.usuario = datos
            elif estado in (401, 403):
                session.pop("backend_token", None)
    return g.usuario

def destino_interno(valor):
    """Reconstruye destinos GET conocidos; nunca redirige a URLs externas."""
    if not isinstance(valor, str) or not valor.startswith("/") or len(valor) > 2048:
        return None
    if "\\" in valor or any(ord(caracter) < 32 or ord(caracter) == 127 for caracter in valor):
        return None
    try:
        partes = urlsplit(valor)
        if partes.scheme or partes.netloc or partes.fragment:
            return None
        ruta = unquote(partes.path)
        if not ruta.startswith("/") or ruta.startswith("//") or "\\" in ruta:
            return None
        endpoint, parametros = app.url_map.bind("localhost").match(ruta, method="GET")
        permitidos = {
            "ver_butacas", "ver_compra", "mis_compras", "ver_comprobante", "ver_qr_cliente",
            "admin_resumen", "admin_peliculas", "admin_funciones", "admin_servicios", "validar_qr",
        }
        if endpoint not in permitidos or any(valor <= 0 for valor in parametros.values() if isinstance(valor, int)):
            return None
        consulta = parse_qs(partes.query, keep_blank_values=True, max_num_fields=20)
        if endpoint == "ver_butacas":
            pelicula = consulta.get("id_pelicula", [""])[0]
            if pelicula:
                parametros["id_pelicula"] = int(pelicula)
                if parametros["id_pelicula"] <= 0:
                    return None
        elif endpoint == "ver_compra":
            parametros["id_funcion"] = int(consulta.get("id_funcion", [""])[0])
            if parametros["id_funcion"] <= 0:
                return None
            parametros["butacas"] = consulta.get("butacas", [""])[0]
        elif endpoint in ("admin_peliculas", "admin_funciones", "admin_servicios"):
            editar = consulta.get("editar", [""])[0]
            if editar:
                parametros["editar"] = int(editar)
                if parametros["editar"] <= 0:
                    return None
            elif consulta.get("nuevo") == ["1"]:
                parametros["nuevo"] = 1
        return url_for(endpoint, **parametros)
    except (ValueError, HTTPException):
        return None


def destino_de_acceso():
    if "next" in request.form or "next" in request.args:
        valor = request.form.get("next") if "next" in request.form else request.args.get("next")
        destino = destino_interno(valor)
        if destino:
            session["destino_acceso"] = destino
        else:
            session.pop("destino_acceso", None)
    return destino_interno(session.get("destino_acceso"))


def contexto_de_acceso(destino):
    if not destino:
        return None
    partes = urlsplit(destino)
    if partes.path.startswith("/butacas/"):
        id_funcion = int(partes.path.rsplit("/", 1)[1])
        butacas = []
    elif partes.path == "/compra":
        consulta = parse_qs(partes.query)
        id_funcion = int(consulta["id_funcion"][0])
        butacas = [valor.strip() for valor in consulta.get("butacas", [""])[0].split(",") if valor.strip()]
    else:
        return None
    datos, estado = llamar_backend("GET", "/funciones")
    funcion = next((fila for fila in lista(datos, "funciones") if fila.get("id_funcion") == id_funcion), None) if estado == 200 else None
    if funcion is None:
        return {"no_disponible": True}
    peliculas, estado_peliculas = llamar_backend("GET", "/peliculas")
    pelicula = next((fila for fila in lista(peliculas, "peliculas") if fila.get("id_pelicula") == funcion.get("id_pelicula")), {}) if estado_peliculas == 200 else {}
    poster = pelicula.get("poster") or ""
    if poster.startswith(("http://", "https://")):
        poster_vista = poster
    elif poster.startswith(("static/", "/static/")):
        poster_vista = urljoin(BACKEND_ORIGEN + "/", poster.lstrip("/"))
    else:
        poster_vista = url_for("static", filename="img/poster_sin_imagen.svg")
    valor_fecha = funcion.get("fecha_hora_inicio", "")
    try:
        try:
            fecha = datetime.fromisoformat(valor_fecha)
        except ValueError:
            fecha = datetime.strptime(valor_fecha, "%a, %d %b %Y %H:%M:%S GMT")
        fecha_visible = fecha.strftime("%d/%m/%Y · %H:%M")
    except (ValueError, TypeError):
        fecha_visible = "Fecha no disponible"
    return {
        "titulo": funcion.get("titulo", "Función seleccionada"),
        "fecha": fecha_visible, "sala": funcion.get("sala_nombre", "Sala no disponible"),
        "precio": funcion.get("precio_base"), "butacas": butacas, "poster": poster_vista,
    }


def requiere_usuario(funcion):
    @wraps(funcion)
    def vista(*args, **kwargs):
        if usuario_actual() is None:
            flash("Iniciá sesión para continuar.", "error")
            destino = destino_interno(request.full_path)
            if destino:
                session["destino_acceso"] = destino
            return redirect(url_for("login", next=destino))
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

@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template("error.html", mensaje="La página que buscás no está disponible. Podés volver a la cartelera."), 404

@app.route("/registro", methods=["GET", "POST"])
def registro():
    destino = destino_de_acceso()
    datos_formulario = {campo: request.form.get(campo, "") for campo in ("nombre", "apellido", "email")}
    error_formulario = None
    estado_pagina = 200
    if request.method == "POST":
        password = request.form.get("password", "")
        if password != request.form.get("confirmar_password", ""):
            error_formulario = "Las contraseñas no coinciden. Volvé a ingresarlas."
            estado_pagina = 400
        else:
            resultado, estado = llamar_backend("POST", "/auth/registro", json={**datos_formulario, "password": password})
            if estado == 201:
                session["email_acceso"] = datos_formulario["email"].strip().lower()
                flash("Tu cuenta fue creada. Iniciá sesión para continuar.", "ok")
                return redirect(url_for("login", next=destino))
            error_formulario = mensaje_error(resultado)
            estado_pagina = estado
    return render_template(
        "registro.html", datos_formulario=datos_formulario,
        error_formulario=error_formulario, destino=destino, contexto=contexto_de_acceso(destino),
    ), estado_pagina


@app.route("/login", methods=["GET", "POST"])
def login():
    destino = destino_de_acceso()
    email_acceso = request.form.get("email", "") if request.method == "POST" else session.pop("email_acceso", "")
    if request.method == "POST":
        datos, estado = llamar_backend("POST", "/auth/login", json={"email": request.form.get("email", ""), "password": request.form.get("password", "")})
        if estado == 200:
            session.clear()
            session["csrf_token"] = secrets.token_hex(24)
            session["backend_token"] = datos["access_token"]
            flash("Sesión iniciada.", "ok")
            usuario = datos.get("usuario", {})
            return redirect(destino or url_for("admin_resumen" if usuario.get("rol", "").strip().casefold() == "administrador" else "index"))
        flash(mensaje_error(datos), "error")
    return render_template("login.html", destino=destino, email_acceso=email_acceso, contexto=contexto_de_acceso(destino))

@app.post("/logout")
def logout():
    datos, estado = llamar_backend("POST", "/auth/logout")
    if estado not in (200, 401):
        flash("No se pudo cerrar la sesión en el servidor. Intentá nuevamente.", "error")
        return redirect(url_for("index"))
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
    return render_template("cartelera.html", peliculas=peliculas, error=estado != 200)

@app.get("/funciones")
def ver_funciones():
    id_pelicula = request.args.get("id_pelicula", type=int)
    datos, estado = llamar_backend("GET", "/funciones", params={"vigentes": "1"})
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
@requiere_usuario
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
        compra["error_entradas"] = estado_entradas != 200

    return render_template("compras.html", compras=compras, error=estado != 200)


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
    servicio_editar = None
    datos_formulario = {"nombre": "", "precio": ""}
    error_formulario = None
    estado_formulario = 200

    if request.method == "POST":
        accion = request.form.get("accion", "crear")
        identificador = request.form.get("id_servicio", type=int)
        if accion not in ("crear", "editar", "eliminar") or (
            accion != "crear" and (not identificador or identificador <= 0)
        ):
            abort(400)

        metodo = {"crear": "POST", "editar": "PUT", "eliminar": "DELETE"}[accion]
        ruta = "/servicios" + (f"/{identificador}" if accion != "crear" else "")
        datos_formulario = {
            "nombre": request.form.get("nombre", ""),
            "precio": request.form.get("precio", ""),
        }
        argumentos = {} if accion == "eliminar" else {"json": datos_formulario}
        resultado, estado = llamar_backend(metodo, ruta, **argumentos)

        if estado in (200, 201):
            flash(mensaje_error(resultado), "ok")
            return redirect(url_for("admin_servicios"))

        if accion == "eliminar":
            flash(mensaje_error(resultado), "error")
            return redirect(url_for("admin_servicios"))

        error_formulario = mensaje_error(resultado)
        estado_formulario = estado
        if accion == "editar":
            servicio_editar = {"id_servicio": identificador}

    datos, estado = llamar_backend("GET", "/servicios")
    error_listado = estado != 200
    servicios = lista(datos, "servicios") if not error_listado else []
    if error_listado:
        flash(mensaje_error(datos), "error")

    if request.method == "GET":
        editar = request.args.get("editar", type=int)
        if editar is not None and not error_listado:
            servicio_editar = next(
                (s for s in servicios if s["id_servicio"] == editar), None
            )
            if servicio_editar is None:
                flash("El servicio que querés editar ya no está disponible.", "error")
                return redirect(url_for("admin_servicios"))
            datos_formulario = {
                "nombre": servicio_editar["nombre"],
                "precio": servicio_editar["precio"],
            }

    return render_template(
        "admin/servicios_admin.html",
        servicios=servicios,
        servicio_editar=servicio_editar,
        datos_formulario=datos_formulario,
        error_formulario=error_formulario,
        error_listado=error_listado,
    ), estado_formulario


@app.route("/admin/peliculas", methods=["GET", "POST"])
@requiere_admin
def admin_peliculas():
    campos = ("titulo", "sinopsis", "poster", "clasificacion", "genero", "duracion_minutos")
    datos_formulario = dict.fromkeys(campos, "")
    datos_formulario["poster"] = "/static/img/default.svg"
    pelicula_editar = None
    resultado_api = None
    busqueda_api = ""
    error_api = None
    error_formulario = None
    estado_pagina = 200
    mostrar_formulario = request.args.get("nuevo") == "1"

    if request.method == "POST":
        accion = request.form.get("accion", "crear")
        if accion in ("buscar", "importar"):
            busqueda_api = request.form.get("titulo", "").strip()
            if not busqueda_api:
                error_api = "Ingresá un título para consultar la API."
                estado_pagina = 400
            else:
                resultado, estado = llamar_backend(
                    "GET" if accion == "buscar" else "POST",
                    "/pelicula", params={"titulo": busqueda_api},
                )
                # El endpoint existente también comunica duplicados con una clave " Error" y HTTP 200.
                rechazo = next((str(valor) for clave, valor in resultado.items()
                                if clave.strip().casefold() == "error"), None) if isinstance(resultado, dict) else None
                if estado not in (200, 201) or rechazo:
                    error_api = rechazo or mensaje_error(resultado)
                    estado_pagina = estado if estado not in (200, 201) else 409
                elif accion == "importar":
                    flash(mensaje_error(resultado), "ok")
                    return redirect(url_for("admin_peliculas"))
                elif isinstance(resultado, dict) and resultado.get("titulo"):
                    resultado_api = resultado
                else:
                    error_api = "La API no devolvió una ficha de película válida."
                    estado_pagina = 502
        elif accion in ("crear", "editar"):
            mostrar_formulario = True
            identificador = request.form.get("id_pelicula", type=int)
            if accion == "editar" and (identificador is None or identificador <= 0):
                abort(400)
            datos_formulario = {campo: request.form.get(campo, "") for campo in campos}
            datos = dict(datos_formulario)
            datos["duracion_minutos"] = request.form.get("duracion_minutos", type=int)
            ruta = "/peliculas" + (f"/{identificador}" if accion == "editar" else "")
            resultado, estado = llamar_backend("PUT" if accion == "editar" else "POST", ruta, json=datos)
            if estado in (200, 201):
                flash(mensaje_error(resultado), "ok")
                return redirect(url_for("admin_peliculas"))
            error_formulario = mensaje_error(resultado)
            estado_pagina = estado
            if accion == "editar":
                pelicula_editar = {"id_pelicula": identificador}
        else:
            abort(400)

    datos, estado = llamar_backend("GET", "/peliculas")
    error_listado = estado != 200
    peliculas = lista(datos, "peliculas") if not error_listado else []
    if error_listado:
        flash(mensaje_error(datos), "error")

    if request.method == "GET" and "editar" in request.args:
        editar = request.args.get("editar", type=int)
        if editar is None or editar <= 0:
            abort(400)
        if not error_listado:
            pelicula_editar = next((p for p in peliculas if p["id_pelicula"] == editar), None)
            if pelicula_editar is None:
                flash("La película que querés editar ya no está disponible.", "error")
                return redirect(url_for("admin_peliculas"))
            mostrar_formulario = True
            datos_formulario = {campo: pelicula_editar.get(campo) or "" for campo in campos}
            duracion = str(datos_formulario["duracion_minutos"]).strip().split()
            datos_formulario["duracion_minutos"] = duracion[0] if duracion else ""

    def poster_para_vista(valor):
        if isinstance(valor, str):
            if valor.startswith(("https://", "http://")):
                return valor
            if valor.startswith(("/static/", "static/")):
                return urljoin(BACKEND_ORIGEN + "/", valor.lstrip("/"))
        return url_for("static", filename="img/poster_sin_imagen.svg")

    return render_template(
        "admin/peliculas_admin.html", peliculas=peliculas,
        pelicula_editar=pelicula_editar, mostrar_formulario=mostrar_formulario,
        datos_formulario=datos_formulario, resultado_api=resultado_api,
        busqueda_api=busqueda_api, error_api=error_api,
        error_formulario=error_formulario, error_listado=error_listado,
        poster_para_vista=poster_para_vista,
    ), estado_pagina


@app.route("/admin/funciones", methods=["GET", "POST"])
@requiere_admin
def admin_funciones():
    campos = ("id_pelicula", "id_sala", "fecha_hora_inicio", "precio_base")
    datos_formulario = dict.fromkeys(campos, "")
    funcion_editar = None
    error_formulario = None
    estado_pagina = 200
    mostrar_formulario = request.args.get("nuevo") == "1"

    if request.method == "POST":
        mostrar_formulario = True
        identificador = request.form.get("id_funcion", type=int)
        if "id_funcion" in request.form and (identificador is None or identificador <= 0):
            abort(400)
        datos_formulario = {campo: request.form.get(campo, "") for campo in campos}
        datos = dict(datos_formulario)
        datos["id_pelicula"] = request.form.get("id_pelicula", type=int)
        datos["id_sala"] = request.form.get("id_sala", type=int)
        ruta = "/funciones" + (f"/{identificador}" if identificador is not None else "")
        resultado, estado = llamar_backend("PUT" if identificador is not None else "POST", ruta, json=datos)
        if estado in (200, 201):
            flash(mensaje_error(resultado), "ok")
            return redirect(url_for("admin_funciones"))
        error_formulario = mensaje_error(resultado)
        estado_pagina = estado
        if identificador is not None:
            funcion_editar = {"id_funcion": identificador}

    p, ep = llamar_backend("GET", "/peliculas")
    f, ef = llamar_backend("GET", "/funciones")
    l, el = llamar_backend("GET", "/locales")
    peliculas = lista(p, "peliculas") if ep == 200 else []
    funciones = [dict(funcion) for funcion in lista(f, "funciones")] if ef == 200 else []
    locales = lista(l, "locales") if el == 200 else []
    salas = []
    errores_carga = []
    if ep != 200:
        errores_carga.append("No se pudieron cargar las películas.")
    if el != 200:
        errores_carga.append("No se pudieron cargar los locales.")
    for local in locales:
        datos, estado = llamar_backend("GET", f"/locales/{local['id_local']}/salas")
        if estado != 200:
            errores_carga.append(f"No se pudieron cargar las salas de {local['nombre']}.")
            continue
        for sala in lista(datos, "salas"):
            salas.append({**sala, "id_local": local["id_local"], "local_nombre": local["nombre"]})
    error_listado = ef != 200
    if error_listado:
        flash("No se pudieron cargar las funciones programadas.", "error")

    def fecha_de_funcion(valor):
        if not isinstance(valor, str):
            return None
        try:
            return datetime.fromisoformat(valor)
        except ValueError:
            try:
                return datetime.strptime(valor, "%a, %d %b %Y %H:%M:%S GMT")
            except ValueError:
                return None

    salas_por_id = {sala["id_sala"]: sala for sala in salas}
    peliculas_por_id = {pelicula["id_pelicula"]: pelicula for pelicula in peliculas}
    for funcion in funciones:
        fecha = fecha_de_funcion(funcion.get("fecha_hora_inicio"))
        funcion["fecha_formulario"] = fecha.strftime("%Y-%m-%dT%H:%M:%S") if fecha else ""
        funcion["fecha_visible"] = fecha.strftime("%d/%m/%Y") if fecha else "Fecha no disponible"
        funcion["hora_visible"] = fecha.strftime("%H:%M:%S" if fecha.second else "%H:%M") if fecha else ""
        sala = salas_por_id.get(funcion.get("id_sala"), {})
        funcion["local_nombre"] = sala.get("local_nombre", "Local no disponible")
        funcion["sala_nombre"] = sala.get("nombre") or funcion.get("sala_nombre", "Sala no disponible")
        duracion = str(peliculas_por_id.get(funcion.get("id_pelicula"), {}).get("duracion_minutos", "")).split()
        funcion["duracion_visible"] = duracion[0] if duracion else ""
    funciones.sort(key=lambda funcion: funcion["fecha_formulario"] or "9999")

    if request.method == "GET" and "editar" in request.args:
        editar = request.args.get("editar", type=int)
        if editar is None or editar <= 0:
            abort(400)
        if not error_listado:
            funcion_editar = next((funcion for funcion in funciones if funcion["id_funcion"] == editar), None)
            if funcion_editar is None:
                flash("La función que querés editar ya no está disponible.", "error")
                return redirect(url_for("admin_funciones"))
            mostrar_formulario = True
            datos_formulario = {campo: str(funcion_editar.get(campo, "")) for campo in campos}
            datos_formulario["fecha_hora_inicio"] = funcion_editar["fecha_formulario"]

    return render_template(
        "admin/funciones_admin.html", peliculas=peliculas, funciones=funciones,
        locales=locales, salas=salas, funcion_editar=funcion_editar,
        datos_formulario=datos_formulario, error_formulario=error_formulario,
        mostrar_formulario=mostrar_formulario, estado_pagina=estado_pagina,
        errores_carga=errores_carga, error_listado=error_listado,
        habilitar_guardado=not errores_carga and bool(peliculas) and bool(salas),
    ), estado_pagina


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
        headers={"Authorization": "Bearer " + session.get("backend_token", "")},
        timeout=10
    )

    if respuesta.status_code != 200:
        abort(respuesta.status_code)

    return Response(respuesta.content, mimetype="image/png")

@app.get("/compras/<int:id_compra>/comprobante")
@requiere_usuario
def ver_comprobante(id_compra):

    comprobante, estado = llamar_backend(
        "GET",
        f"/compras/{id_compra}/comprobante"
    )

    if estado != 200:
        abort(estado)

    return render_template(
        "comprobante.html",
        comprobante=comprobante
    )


if __name__ == "__main__":
    app.run("127.0.0.1",port=8080,debug=os.environ.get("FLASK_DEBUG") == "1")