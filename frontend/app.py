import os
import secrets
from functools import wraps
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlsplit, unquote, parse_qs
from werkzeug.exceptions import HTTPException

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for, flash, g, abort, send_file

from flask import Response
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, 
    TableStyle, Image)

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
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
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
        elif endpoint == "mis_compras":
            id_compra = consulta.get("cancelar", [None])[0]

            if id_compra is not None:
                id_compra = int(id_compra)

                if id_compra <= 0:
                    return None

                parametros["cancelar"] = id_compra
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

@app.errorhandler(413)
def carga_demasiado_grande(error):
    return render_template(
        "error.html",
        mensaje="La imagen o los datos enviados superan el límite de 5 MB. Elegí una imagen más liviana y volvé a intentarlo.",
    ), 413

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
    datos, estado = llamar_backend("GET", "/peliculas")
    peliculas, vistos = [], set()
    for peli in lista(datos, "peliculas"):
        if peli["id_pelicula"] not in vistos:
            peli["duracion"] = peli.get("duracion_minutos")

            poster = peli.get("poster", "")
            if poster and not poster.startswith(("http://", "https://")):
                ruta_poster = poster.lstrip("/")
                if ruta_poster.startswith("static/img/demo_"):
                    peli["poster"] = url_for(
                        "static",
                        filename=ruta_poster.removeprefix("static/")
                    )
                elif poster:
                    peli["poster"] = urljoin(
                        BACKEND_ORIGEN + "/",
                        ruta_poster
                    )
            peliculas.append(peli)
            vistos.add(peli["id_pelicula"])
    if estado != 200:
        flash(mensaje_error(datos), "error")
    return render_template("cartelera.html", peliculas=peliculas, error=estado != 200)

@app.get("/funciones")
def ver_funciones():
    id_pelicula = request.args.get("id_pelicula", type=int)

    datos, estado = llamar_backend("GET", "/cartelera")

    peliculas_cartelera = lista(datos, "cartelera")

    funciones = [
        f for f in peliculas_cartelera
        if id_pelicula and f.get("id_pelicula") == id_pelicula
    ]

    pelicula = funciones[0].copy() if funciones else {}

    if id_pelicula and (not pelicula or not pelicula.get("poster")):
        datos_peliculas, estado_peliculas = llamar_backend("GET", "/peliculas")
        catalogo = lista(datos_peliculas, "peliculas")
        ficha = next(
            (p for p in catalogo
             if p.get("id_pelicula") == id_pelicula),
            {}
        )

        if not pelicula:
            pelicula = ficha.copy()
        elif ficha.get("poster"):
            pelicula["poster"] = ficha["poster"]

    if pelicula:
        poster = pelicula.get("poster", "")

        if poster and not poster.startswith(("http://", "https://")):
            pelicula["poster"] = urljoin(
                BACKEND_ORIGEN + "/",
                poster.lstrip("/")
            )

    for funcion in funciones:
        try:
            fecha = datetime.strptime(
            funcion["fecha_hora_inicio"],
            "%a, %d %b %Y %H:%M:%S GMT"
            )

            dias = [
                "lunes", "martes", "miércoles", "jueves",
                "viernes", "sábado", "domingo"
            ]

            meses_cortos = [
                "Ene", "Feb", "Mar", "Abr", "May", "Jun",
                "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
            ]

            meses_cortos2 = [
                "ene.", "feb.", "mar.", "abr.",
                "may.", "jun.", "jul.", "ago.",
                "sep.", "oct.", "nov.", "dic."
            ]

            meses_largos = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre",
                "Diciembre"
            ]
            funcion["mes_nombre"] = meses_largos[fecha.month - 1]
            funcion["anio"] = fecha.year

            funcion["fecha"] = (
                f"{fecha.day} {meses_cortos[fecha.month - 1]}"
            )

            funcion["fecha_completa"] = (
                f"{dias[fecha.weekday()].capitalize()} "
                f"{fecha.day} de {meses_cortos2[fecha.month - 1]}"
            )

            funcion["horario"] = fecha.strftime("%H:%M")

        except (ValueError, TypeError):
            funcion["fecha"] = funcion.get("fecha_hora_inicio", "")
            funcion["fecha_completa"] = funcion["fecha"]
            funcion["horario"] = ""


    return render_template(
        "funciones.html",
        funciones=funciones,
        pelicula=pelicula,
        id_pelicula=id_pelicula,
        error=estado != 200
    )

@app.get("/butacas/<int:id_funcion>")
@requiere_usuario
def ver_butacas(id_funcion):
    
    datos_butacas, estado_butacas = llamar_backend(
        "GET", f"/funciones/{id_funcion}/butacas"
    )
    butacas = lista(datos_butacas, "butacas")
    
    datos_cartelera, estado_cartelera = llamar_backend("GET", "/cartelera")
    funciones_cartelera = lista(datos_cartelera, "cartelera")

    funcion = next(
        (f for f in funciones_cartelera
         if f.get("id_funcion") == id_funcion),
        None
    )

    if funcion:
        # Preparar el póster
        poster = funcion.get("poster", "")
        if poster and not poster.startswith(("http://", "https://")):
            funcion["poster"] = urljoin(
                BACKEND_ORIGEN + "/",
                poster.lstrip("/")
            )

        try:

            fecha = datetime.strptime(
            funcion["fecha_hora_inicio"],
            "%a, %d %b %Y %H:%M:%S GMT"
            )

            dias = [
                "lunes", "martes", "miércoles", "jueves",
                "viernes", "sábado", "domingo"
            ]
            meses_cortos = [
                "ene", "feb", "mar", "abr", "may", "jun",
                "jul", "ago", "sep", "oct", "nov", "dic"
            ]
            dia_semana = dias[fecha.weekday()].capitalize()
            mes = meses_cortos[fecha.month - 1]

            funcion["fecha"] = (
                f"{dia_semana} {fecha.day} {mes}, {fecha.year}"
            )

            funcion["horario"] = fecha.strftime("%H:%M")
        except (ValueError, TypeError):
            funcion["fecha"] = funcion.get("fecha_hora_inicio", "")
            funcion["horario"] = ""

    return render_template(
        "butacas.html",
        butacas=butacas,
        pelicula=funcion or {"titulo": "Selección de butacas"},
        funcion=funcion,
        id_funcion=id_funcion,
        id_pelicula=funcion.get("id_pelicula") if funcion else None,
        error=(
            estado_butacas != 200
            or estado_cartelera != 200
            or funcion is None
        )
    )


def obtener_servicios_seleccionados(texto):
    if not texto:
        return []

    servicios = []
    ids = set()

    for elemento in texto.split(","):
        partes = elemento.split(":")

        if len(partes) != 2:
            raise ValueError("Formato de servicios inválido")

        id_servicio = int(partes[0])
        cantidad = int(partes[1])

        if id_servicio <= 0 or cantidad <= 0 or id_servicio in ids:
            raise ValueError("Selección de servicios inválida")

        servicios.append({
            "id_servicio": id_servicio,
            "cantidad": cantidad
        })

        ids.add(id_servicio)

    return servicios


@app.get("/compra")
@requiere_usuario
def ver_compra():
    id_funcion = request.args.get("id_funcion", type=int)

    ids_butacas = [
        b.strip()
        for b in request.args.get("butacas", "").split(",")
        if b.strip()
    ]

    if not id_funcion or id_funcion <= 0 or not ids_butacas:
        return render_template(
            "compra.html",
            error=True,
            id_funcion=id_funcion,
            butacas=ids_butacas
        )

    servicios_texto = request.args.get("servicios", "")

    try:
        servicios_seleccionados = obtener_servicios_seleccionados(servicios_texto)
    except ValueError:
        flash("La selección de servicios no es válida", "error")
        return redirect(url_for(
            "ver_servicios",
            id_funcion=id_funcion,
            butacas=",".join(ids_butacas)
        ))


    datos_cartelera, estado_cartelera = llamar_backend(
        "GET", "/cartelera"
    )
    funciones = lista(datos_cartelera, "cartelera")

    funcion = next(
        (
            f for f in funciones
            if f.get("id_funcion") == id_funcion
        ),
        None
    )

    if estado_cartelera != 200 or not funcion:
        return render_template(
            "compra.html",
            error=True,
            id_funcion=id_funcion,
            butacas=ids_butacas
        )

    
    # Recuperar el póster desde la función o desde el catálogo de películas.
    poster = funcion.get("poster") or ""
    if not poster:
        peliculas, estado_peliculas = llamar_backend("GET", "/peliculas")
        if estado_peliculas == 200:
            pelicula = next(
                (
                    p for p in lista(peliculas, "peliculas")
                    if p.get("id_pelicula") == funcion.get("id_pelicula")
                ),
                {}
            )
            poster = pelicula.get("poster") or ""

    if poster.startswith(("http://", "https://")):
        funcion["poster"] = poster
    elif poster:
        ruta_poster = poster.lstrip("/")
        archivo_local = (
            Path(__file__).resolve().parent
            / "static"
            / ruta_poster.removeprefix("static/")
        )
        if ruta_poster.startswith("static/") and archivo_local.is_file():
            funcion["poster"] = url_for(
                "static",
                filename=ruta_poster.removeprefix("static/")
            )
        else:
            funcion["poster"] = urljoin(
                BACKEND_ORIGEN + "/",
                ruta_poster
            )
    else:
        funcion["poster"] = url_for(
            "static",
            filename="img/poster_sin_imagen.svg"
        )

    
    try:
        fecha = datetime.strptime(
            funcion["fecha_hora_inicio"],
            "%a, %d %b %Y %H:%M:%S GMT"
        )

        dias = [
            "lunes", "martes", "miércoles", "jueves",
            "viernes", "sábado", "domingo"
        ]
        meses = [
            "enero", "febrero", "marzo", "abril",
            "mayo", "junio", "julio", "agosto",
            "septiembre", "octubre", "noviembre", "diciembre"
        ]

        funcion["fecha"] = (
            f"{dias[fecha.weekday()]} {fecha.day} "
            f"de {meses[fecha.month - 1]} de {fecha.year}"
        )
        funcion["horario"] = fecha.strftime("%H:%M")

    except (ValueError, TypeError, KeyError):
        funcion["fecha"] = funcion.get("fecha_hora_inicio", "")
        funcion["horario"] = ""

    
    datos_butacas, estado_butacas = llamar_backend(
        "GET",
        f"/funciones/{id_funcion}/butacas"
    )
    butacas_disponibles = lista(datos_butacas, "butacas")

    
    mapa_butacas = {
        str(b.get("id_butaca")): f"{b.get('fila')}{b.get('numero')}"
        for b in butacas_disponibles
    }

    detalle_butacas = [
        mapa_butacas.get(id_butaca, id_butaca)
        for id_butaca in ids_butacas
    ]

    precio_unitario = float(funcion.get("precio_base") or 0)
    total = precio_unitario * len(ids_butacas)

    detalle_servicios = []

    if servicios_seleccionados:
        datos_servicios, estado_servicios = llamar_backend("GET", "/servicios")

        if estado_servicios != 200:
            flash("No se pudieron cargar los servicios seleccionados", "error")
            return redirect(url_for(
                "ver_servicios",
                id_funcion=id_funcion,
                butacas=",".join(ids_butacas)
            ))

        servicios_disponibles = lista(datos_servicios, "servicios")

        for seleccionado in servicios_seleccionados:
            servicio = next(
                (
                    s for s in servicios_disponibles
                    if s["id_servicio"] == seleccionado["id_servicio"]
                ),
                None
            )

            if servicio is None:
                flash("Uno de los servicios ya no está disponible", "error")
                return redirect(url_for(
                    "ver_servicios",
                    id_funcion=id_funcion,
                    butacas=",".join(ids_butacas)
                ))

            cantidad = seleccionado["cantidad"]
            precio = float(servicio["precio"])
            subtotal = precio * cantidad

            detalle_servicios.append({
                "nombre": servicio["nombre"],
                "cantidad": cantidad,
                "subtotal": subtotal
            })

            total += subtotal

    # Datos de la persona autenticada.
    usuario = usuario_actual() or {}
    if isinstance(usuario, dict):
        usuario = usuario.get("usuario", usuario)

    return render_template(
        "compra.html",
        id_funcion=id_funcion,
        butacas=ids_butacas,
        detalle_butacas=detalle_butacas,
        funcion=funcion,
        precio_unitario=precio_unitario,
        total=total,
        usuario=usuario,
        error=estado_butacas != 200,
        servicios_seleccionados=servicios_seleccionados,
        detalle_servicios=detalle_servicios,
        servicios_texto=servicios_texto
    )

def pago_aprobado():
    return os.environ.get("SIMULAR_PAGO_RECHAZADO") != "1"

@app.post("/procesar-compra")
@requiere_usuario
def procesar_compra():

    id_funcion = request.form.get("id_funcion", type=int)
    butacas_texto = request.form.get("butacas", "")

    if not id_funcion or id_funcion <= 0:
        flash("La función seleccionada no es válida.", "error")
        return redirect(url_for("index"))

    try:
        ids_butacas = [
            int(b.strip())
            for b in butacas_texto.split(",")
            if b.strip()
        ]
    except ValueError:
        flash("La selección de butacas no es válida.", "error")
        return redirect(url_for("ver_butacas", id_funcion=id_funcion))

    if (
        not ids_butacas
        or any(id_butaca <= 0 for id_butaca in ids_butacas)
        or len(ids_butacas) != len(set(ids_butacas))
    ):
        flash("La selección de butacas no es válida.", "error")
        return redirect(url_for("ver_butacas", id_funcion=id_funcion))

    servicios_texto = request.form.get("servicios", "")

    try:
        servicios_seleccionados = obtener_servicios_seleccionados(servicios_texto)
    except ValueError:
        flash("La selección de servicios no es válida", "error")
        return redirect(url_for(
            "ver_servicios",
            id_funcion=id_funcion,
            butacas=butacas_texto
        ))

    if request.form.get("metodo_pago") != "tarjeta":
        flash("Selecciona un método de pago valido", "error")
        return redirect(url_for(
            "ver_compra",
            id_funcion=id_funcion,
            butacas=butacas_texto
        ))

    if not pago_aprobado():
        reserva_pendiente = session.get("reserva_pendiente")

        if reserva_pendiente:
            misma_seleccion = (
                reserva_pendiente.get("id_funcion") == id_funcion
                and reserva_pendiente.get("butacas") == ids_butacas
                and reserva_pendiente.get("servicios", []) == servicios_seleccionados
            )

            if not misma_seleccion:
                flash(
                    "El pago fue rechazado. Tenés otra reserva pendiente "
                    "que no fue modificada.",
                    "error"
                )
                return redirect(url_for("mis_compras"))

        if reserva_pendiente:
            id_compra = reserva_pendiente.get("id_compra")

            if not id_compra:
                flash("No se pudo identificar la reserva pendiente.", "error")
                return redirect(url_for("mis_compras"))

            resultado, estado = llamar_backend(
                "POST",
                f"/reservas/{id_compra}/rechazar"
            )

            if estado != 200:
                flash(
                    "El pago fue rechazado, pero no se pudo liberar "
                    "la reserva: " + mensaje_error(resultado),
                    "error"
                )
                return redirect(url_for("mis_compras"))

            session.pop("reserva_pendiente", None)

        flash("El pago fue rechazado. Intentá nuevamente.", "error")

        return redirect(url_for(
            "ver_compra",
            id_funcion=id_funcion,
            butacas=butacas_texto,
            servicios=servicios_texto
        ))


    reserva_pendiente = session.get("reserva_pendiente")

    if reserva_pendiente:
        compras, estado_compras = llamar_backend("GET", "/compras")

        if estado_compras != 200:
            flash("No se pudo verificar tu reserva anterior. Revisa Mis compras", "error")
            return redirect(url_for("mis_compras"))

        compra_guardada = next(
            (
                compra for compra in lista(compras, "compras")
                if compra.get("id_compra") == reserva_pendiente["id_compra"]
            ),
            None
        )

        if compra_guardada and compra_guardada["estado"] in ("aprobada", "confirmada"):
            session.pop("reserva_pendiente", None)
            return redirect(url_for(
                "ver_comprobante",
                id_compra=reserva_pendiente["id_compra"]
            ))

        if not compra_guardada or compra_guardada["estado"] in ("expirada", "rechazada", "cancelada"):
            session.pop("reserva_pendiente", None)
            reserva_pendiente = None

        elif compra_guardada["estado"] != "pendiente":
            flash("No se pudo determinar el estado de tu reserva", "error")
            return redirect(url_for("mis_compras"))

    if reserva_pendiente:
        id_compra = reserva_pendiente["id_compra"]

        if reserva_pendiente["id_funcion"] != id_funcion:
            flash(
                "Ya tenés una reserva pendiente para otra función"
                "Terminala antes de realizar una nueva",
                "error"
            )
            return redirect(url_for("index"))

        cambio_butacas = reserva_pendiente["butacas"] != ids_butacas
        cambio_servicios = (
            reserva_pendiente.get("servicios", []) != servicios_seleccionados
        )

        if cambio_butacas or cambio_servicios:
            resultado, estado = llamar_backend(
                "PUT",
                f"/reservas/{id_compra}",
                json={
                    "butacas": ids_butacas,
                    "servicios": servicios_seleccionados
                }
            )

            if estado != 200:
                flash(
                    "No se pudo modificar la reserva: "
                    + mensaje_error(resultado),
                    "error"
                )
                return redirect(url_for(
                    "ver_compra",
                    id_funcion=id_funcion,
                    butacas=butacas_texto,
                    servicios=servicios_texto
                ))

            session["reserva_pendiente"] = {
                "id_compra": id_compra,
                "id_funcion": id_funcion,
                "butacas": ids_butacas,
                "servicios": servicios_seleccionados
            }

    else:
        resultado, estado = llamar_backend(
            "POST",
            f"/funciones/{id_funcion}/reservas",
            json={
                "butacas": ids_butacas,
                "servicios": servicios_seleccionados
            }
        )

        if estado != 201:
            flash(mensaje_error(resultado), "error")
            return redirect(url_for(
                "ver_butacas",
                id_funcion=id_funcion
            ))

        reserva = resultado.get("reserva", {}) if isinstance(resultado, dict) else {}
        id_compra = reserva.get("id_compra")

        if not id_compra:
            flash(
                "No se pudo recuperar el identificador de la reserva. "
                "Consultá tus compras antes de volver a intentar.",
                "error"
            )
            return redirect(url_for("mis_compras"))

        session["reserva_pendiente"] = {
            "id_compra": id_compra,
            "id_funcion": id_funcion,
            "butacas": ids_butacas,
            "servicios": servicios_seleccionados
    }

    resultado, estado = llamar_backend(
        "POST",
        f"/compras/{id_compra}/confirmar"
    )



    if estado == 200:
        session.pop("reserva_pendiente", None)

        datos_compra = resultado.get("compra", resultado)
        mensaje_correo = datos_compra.get("mensaje_correo")

        if mensaje_correo:
            flash(mensaje_correo, "ok")
        else:
            flash(
                "La compra fue confirmada. Podés consultar tus entradas desde el comprobante.",
                "ok"
            )

        return redirect(url_for(
            "ver_comprobante",
            id_compra=id_compra
        ))

    compras, estado_compras = llamar_backend("GET", "/compras")

    if estado_compras == 200:

        compra_guardada = next(
            (
                compra for compra in lista(compras, "compras")
                if compra.get("id_compra") == id_compra
            ),
            None
        )

        if compra_guardada:

            if compra_guardada["estado"] in ("aprobada", "confirmada"):
                session.pop("reserva_pendiente", None)

                return redirect(url_for(
                    "ver_comprobante",
                    id_compra=id_compra
                ))

            if compra_guardada["estado"] in ("expirada", "rechazada", "cancelada"):
                session.pop("reserva_pendiente", None)

                flash(
                    "La reserva ya no está vigente. Selecciona nuevamente tus butacas",
                    "error"
                )

                return redirect(url_for(
                    "ver_butacas",
                    id_funcion=id_funcion
                ))

    flash(
        "No se pudo confirmar la compra: " + mensaje_error(resultado),
        "error"
    )

    return redirect(url_for(
        "ver_compra",
        id_funcion=id_funcion,
        butacas=butacas_texto,
        servicios=servicios_texto
    ))

@app.route("/servicios", methods=["GET", "POST"])
def ver_servicios():
    id_funcion = request.values.get("id_funcion", type=int)
    bruto_butacas = request.values.get("butacas", "")

    if isinstance(bruto_butacas, str):
        ids_butacas = [
            b.strip() for b in bruto_butacas.split(",") if b.strip()
        ]
    else:
        ids_butacas = bruto_butacas


    datos, estado = llamar_backend("GET", "/servicios")
    servicios = lista(datos, "servicios")
    for s in servicios:
        img = s.get("imagen")
        if img:
            if img.startswith(("http://", "https://")):
                s["imagen_url"] = img
            else:
                ruta_limpia = img.lstrip("/")
                if not ruta_limpia.startswith("static/"):
                    ruta_limpia = f"static/{ruta_limpia}"
                s["imagen_url"] = f"{BACKEND_ORIGEN}/{ruta_limpia}"
        else:
            s["imagen_url"] = None


    if not id_funcion and not ids_butacas:
        return render_template(
            "servicios.html",
            servicios=servicios,
            funcion=None,
            id_funcion=None,
            ids_butacas=[],
            detalle_butacas=[],
            servicios_seleccionados=[],
            modo_catalogo=True,
            error=estado != 200
        )


    if usuario_actual() is None:
        flash("Iniciá sesión para continuar con tu compra.", "error")
        destino = destino_interno(request.full_path)
        if destino:
            session["destino_acceso"] = destino
        return redirect(url_for("login", next=destino))

    
    if not id_funcion or not ids_butacas:
        return redirect(url_for("ver_funciones"))

    datos_cartelera, estado_cartelera = llamar_backend("GET", "/cartelera")
    funciones = lista(datos_cartelera, "cartelera")
    funcion = next(
        (f for f in funciones if f.get("id_funcion") == id_funcion),
        None
    )

    if not funcion:
        flash("No encontramos la función solicitada.", "error")
        return redirect(url_for("ver_funciones"))

    try:
        fecha = datetime.strptime(
            funcion["fecha_hora_inicio"],
            "%a, %d %b %Y %H:%M:%S GMT"
        )
        dias_cortos = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        meses_cortos = [
            "ene", "feb", "mar", "abr", "may", "jun",
            "jul", "ago", "sep", "oct", "nov", "dic"
        ]
        funcion["fecha_corta"] = (
            f"{dias_cortos[fecha.weekday()]} {fecha.day} "
            f"{meses_cortos[fecha.month - 1].capitalize()} · "
            f"{fecha.strftime('%H:%M')}"
        )
    except (ValueError, TypeError, KeyError):
        funcion["fecha_corta"] = funcion.get("fecha_hora_inicio", "")

    datos_butacas, estado_butacas = llamar_backend(
        "GET", f"/funciones/{id_funcion}/butacas"
    )
    butacas_disponibles = lista(datos_butacas, "butacas")

    mapa_butacas = {
        str(b.get("id_butaca")): f"{b.get('fila')}{b.get('numero')}"
        for b in butacas_disponibles
    }
    detalle_butacas = [
        mapa_butacas.get(id_b, id_b) for id_b in ids_butacas
    ]

    servicios_seleccionados = request.values.getlist("servicios")

    return render_template(
        "servicios.html",
        servicios=servicios,
        funcion=funcion,
        id_funcion=id_funcion,
        ids_butacas=ids_butacas,
        detalle_butacas=detalle_butacas,
        servicios_seleccionados=servicios_seleccionados,
        modo_catalogo=False,
        error=(
            estado != 200
            or estado_cartelera != 200
            or estado_butacas != 200
        )
    )

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

    id_compra_cancelar = request.args.get("cancelar", type=int)

    compra_cancelable = next(
        (
            compra for compra in compras
            if compra["id_compra"] == id_compra_cancelar
            and compra["estado"].lower() in ("aprobada", "confirmada")
        ),
        None
    )

    if id_compra_cancelar is not None and compra_cancelable is None and estado == 200:
        flash("La compra indicada no existe o no se puede cancelar", "error")

    return render_template(
        "compras.html",
        compras=compras,
        error=estado != 200,
        id_compra_cancelar=compra_cancelable["id_compra"] if compra_cancelable else None
    )

@app.post("/mis-compras/<int:id_compra>/cancelar")
@requiere_usuario
def cancelar_compra_frontend(id_compra):
    datos, estado = llamar_backend(
        "POST",
        f"/compras/{id_compra}/cancelar"
    )

    if estado == 200:
        flash(mensaje_error(datos), "ok")
    else:
        flash(mensaje_error(datos), "error")

    return redirect(url_for("mis_compras"))



@app.get("/admin")
@requiere_admin
def admin_resumen():
    ventas, ev = llamar_backend("GET", "/estadisticas/ventas")
    ocupacion, eo = llamar_backend("GET", "/estadisticas/ocupacion")

    return render_template(
        "admin/resumen_admin.html",
        ventas=ventas if ev == 200 else {},
        ocupacion=ocupacion if eo == 200 else {},
        ventas_ok=ev == 200,
        ocupacion_ok=eo == 200
    )

@app.route("/admin/servicios", methods=["GET", "POST"])
@requiere_admin
def admin_servicios():
    servicio_editar = None
    datos_formulario = {"nombre": "", "descripcion": "", "precio": ""}
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
            "descripcion": request.form.get("descripcion", ""),
            "precio": request.form.get("precio", ""),
        }
        
        argumentos = {}
        if accion != "eliminar":
            argumentos["data"] = datos_formulario
            archivo = request.files.get("imagen")
            if archivo and archivo.filename != "":
                argumentos["files"] = {"imagen": (archivo.filename, archivo.stream, archivo.mimetype)}

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
    for s in servicios:
        img = s.get("imagen")
        if img:
            if img.startswith(("http://", "https://")):
                s["imagen_url"] = img
            else:
                ruta_limpia = img.lstrip("/")
                if not ruta_limpia.startswith("static/"):
                    ruta_limpia = f"static/{ruta_limpia}"
                s["imagen_url"] = f"{BACKEND_ORIGEN}/{ruta_limpia}"
        else:
            s["imagen_url"] = None

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
                "descripcion": servicio_editar["descripcion"],
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




@app.route("/admin/locales", methods=["GET", "POST"])
@requiere_admin
def admin_locales():
    datos_formulario = {"nombre": "", "direccion": ""}
    error_formulario = None

    if request.method == "POST":
        datos_formulario = {
            "nombre": request.form.get("nombre", "").strip(),
            "direccion": request.form.get("direccion", "").strip(),
        }
        resultado, estado = llamar_backend("POST", "/locales", json=datos_formulario)
        if estado in (200, 201):
            flash(mensaje_error(resultado), "ok")
            return redirect(url_for("admin_locales"))
        error_formulario = mensaje_error(resultado)

    datos, estado = llamar_backend("GET", "/locales")
    locales = lista(datos, "locales") if estado == 200 else []

    return render_template(
        "admin/locales_admin.html",
        locales=locales,
        datos_formulario=datos_formulario,
        error_formulario=error_formulario,
        error_listado=estado != 200,
    )


@app.route("/admin/salas", methods=["GET", "POST"])
@requiere_admin
def admin_salas():
    datos_formulario = {"id_local": "", "nombre": "", "capacidad": ""}
    error_formulario = None

    if request.method == "POST":
        datos_formulario = {
            "id_local": request.form.get("id_local", ""),
            "nombre": request.form.get("nombre", "").strip(),
            "capacidad": request.form.get("capacidad", "").strip(),
        }
        id_local = request.form.get("id_local", type=int)
        capacidad = request.form.get("capacidad", type=int)

        if not id_local or id_local <= 0 or not capacidad or capacidad <= 0:
            error_formulario = "Seleccioná un local e ingresá una capacidad válida."
        else:
            resultado, estado = llamar_backend(
                "POST",
                f"/locales/{id_local}/salas",
                json={"nombre": datos_formulario["nombre"], "capacidad": capacidad},
            )
            if estado in (200, 201):
                flash(mensaje_error(resultado), "ok")
                return redirect(url_for("admin_salas", local=id_local))
            error_formulario = mensaje_error(resultado)

    datos, estado = llamar_backend("GET", "/locales")
    locales = lista(datos, "locales") if estado == 200 else []
    salas = []
    errores_carga = []

    for local in locales:
        respuesta, codigo = llamar_backend("GET", f"/locales/{local['id_local']}/salas")
        if codigo == 200:
            for sala in lista(respuesta, "salas"):
                salas.append({**sala, "local_nombre": local["nombre"]})
        else:
            errores_carga.append(f"No se pudieron cargar las salas de {local['nombre']}.")

    return render_template(
        "admin/salas_admin.html",
        locales=locales,
        salas=salas,
        datos_formulario=datos_formulario,
        error_formulario=error_formulario,
        errores_carga=errores_carga,
        error_locales=estado != 200,
    )


@app.route("/admin/salas/<int:id_sala>/butacas", methods=["GET", "POST"])
@requiere_admin
def admin_butacas(id_sala):
    if id_sala <= 0:
        abort(400)

    sala_seleccionada = None
    locales_datos, estado_locales = llamar_backend("GET", "/locales")
    locales = lista(locales_datos, "locales") if estado_locales == 200 else []

    for local in locales:
        datos, estado = llamar_backend("GET", f"/locales/{local['id_local']}/salas")
        if estado == 200:
            for sala in lista(datos, "salas"):
                if sala["id_sala"] == id_sala:
                    sala_seleccionada = {**sala, "local_nombre": local["nombre"]}
                    break
        if sala_seleccionada:
            break

    if sala_seleccionada is None:
        flash("La sala seleccionada no existe o no está disponible.", "error")
        return redirect(url_for("admin_salas"))

    error_formulario = None
    distribucion = ""

    if request.method == "POST":
        distribucion = request.form.get("distribucion", "").strip()
        butacas = []
        filas_utilizadas = set()

        try:
            if not distribucion:
                raise ValueError

            for segmento in distribucion.split(","):
                partes = segmento.strip().split(":")

                if len(partes) != 2:
                    raise ValueError

                fila = partes[0].strip().upper()
                cantidad = int(partes[1].strip())

                if (
                    not fila
                    or not fila.isalpha()
                    or len(fila) > 5
                    or cantidad <= 0
                    or fila in filas_utilizadas
                ):
                    raise ValueError

                filas_utilizadas.add(fila)

                for numero in range(1, cantidad + 1):
                    butacas.append({"fila": fila, "numero": numero})

            if len(butacas) != int(sala_seleccionada["capacidad"]):
                raise ValueError

        except (ValueError, TypeError):
            error_formulario = (
                "Ingresá una distribución válida, por ejemplo A:10,B:10. "
                "No repitas filas y verificá que la suma coincida "
                "con la capacidad de la sala."
            )
        else:
            resultado, estado = llamar_backend(
                "POST",
                f"/salas/{id_sala}/butacas",
                json={"butacas": butacas},
            )
            if estado in (200, 201):
                flash(mensaje_error(resultado), "ok")
                return redirect(url_for("admin_salas"))
            error_formulario = mensaje_error(resultado)

    return render_template(
        "admin/butacas_admin.html",
        sala=sala_seleccionada,
        distribucion=distribucion,
        error_formulario=error_formulario,
    )

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

@app.get("/compras/<int:id_compra>/comprobante/pdf")
@requiere_usuario
def descargar_comprobante_pdf(id_compra):

    comprobante, estado = llamar_backend(
        "GET",
        f"/compras/{id_compra}/comprobante"
    )

    if estado != 200:
        abort(estado)

    compra = comprobante["compra"]
    entradas = comprobante["entradas"]
    servicios = comprobante.get("servicios", [])

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    estilos = getSampleStyleSheet()
    elementos = []

    titulo = ParagraphStyle(
        "TituloCine",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#702f24"),
        fontSize=20,
        spaceAfter=15
    )

    elementos.append(Paragraph("CINE PARADISO", titulo))
    elementos.append(Paragraph(
        f"Comprobante de compra N° {compra['id_compra']}",
        estilos["Heading2"]
    ))

    elementos.append(Spacer(1, 10))

    datos_compra = [
        ["Cliente", f"{escape(str(compra['nombre']))} {escape(str(compra['apellido']))}"],
        ["Email", escape(str(compra["email"]))],
        ["Fecha", escape(str(compra["fecha_hora"]))],
        ["Estado", escape(str(compra["estado"]))],
        ["Total", f"$ {compra['total']}"]
    ]

    tabla_compra = Table(datos_compra, colWidths=[35 * mm, 120 * mm])

    tabla_compra.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eee4d5")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))

    elementos.append(tabla_compra)
    elementos.append(Spacer(1, 18))
    elementos.append(Paragraph("ENTRADAS", estilos["Heading2"]))

    if compra["estado"] in ("aprobada", "confirmada"):

        for entrada in entradas:

            elementos.append(Paragraph(
                f"<b>{escape(str(entrada['pelicula']))}</b>",
                estilos["Heading3"]
            ))

            datos_entrada = [
                ["Función", escape(str(entrada["fecha_hora_inicio"]))],
                ["Cine", escape(str(entrada["local"]))],
                ["Dirección", escape(str(entrada.get("direccion", "No disponible")))],
                ["Sala", escape(str(entrada["sala"]))],
                ["Butaca", f"{escape(str(entrada['fila']))}{escape(str(entrada['numero']))}"]
            ]

            tabla_entrada = Table(
                datos_entrada,
                colWidths=[35 * mm, 120 * mm]
            )

            tabla_entrada.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("PADDING", (0, 0), (-1, -1), 7)
            ]))

            elementos.append(tabla_entrada)
            elementos.append(Spacer(1, 8))

            respuesta_qr = requests.get(
                f"{BACKEND_URL}/qr/{entrada['id_entrada']}",
                headers={
                    "Authorization": "Bearer " + session.get("backend_token", "")
                },
                timeout=15
            )

            if respuesta_qr.status_code != 200:
                abort(respuesta_qr.status_code)

            imagen_qr = Image(
                BytesIO(respuesta_qr.content),
                width=35 * mm,
                height=35 * mm
            )

            elementos.append(imagen_qr)
            elementos.append(Spacer(1, 15))

    elementos.append(Paragraph(
        "SERVICIOS ADICIONALES",
        estilos["Heading2"]
    ))

    if servicios:
        datos_servicios = [["Servicio", "Cantidad", "Subtotal"]]

        for servicio in servicios:
            datos_servicios.append([
                escape(str(servicio["nombre"])),
                str(servicio["cantidad"]),
                f"$ {servicio['subtotal']}"
            ])

        tabla_servicios = Table(
            datos_servicios,
            colWidths=[80 * mm, 30 * mm, 45 * mm]
        )

        tabla_servicios.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eee4d5")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 8)
        ]))

        elementos.append(tabla_servicios)

    else:
        elementos.append(Paragraph(
            "No se compraron servicios adicionales.",
            estilos["Normal"]
        ))

    elementos.append(Spacer(1, 15))

    documento.build(elementos)

    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"comprobante_{id_compra}.pdf"
    )

if __name__ == "__main__":
    app.run("127.0.0.1",port=8080,debug=os.environ.get("FLASK_DEBUG") == "1")
