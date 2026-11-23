from functools import wraps
from datetime import datetime
from urllib.parse import urljoin, urlsplit, unquote, parse_qs
from werkzeug.exceptions import HTTPException
from flask import request, session, redirect, url_for, flash, g, abort, current_app

from frontend.utils.api_client import llamar_backend, lista, BACKEND_ORIGEN


def usuario_actual():
    #"""Obtiene y almacena en el contexto `g` los datos del usuario logueado."""
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
    #"""Reconstruye destinos GET conocidos; nunca redirige a URLs externas."""
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

        # Uso de current_app para desacoplar de app.py
        endpoint, parametros = current_app.url_map.bind("localhost").match(ruta, method="GET")
        permitidos = {
            "ver_butacas", "ver_compra", "mis_compras", "ver_comprobante", "ver_qr_cliente",
            "admin_resumen", "admin_peliculas", "admin_funciones", "admin_servicios",
            "validar_qr", "ver_resenas_pelicula",
        }
        if endpoint not in permitidos or any(val <= 0 for val in parametros.values() if isinstance(val, int)):
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
    #"""Obtiene y guarda el destino de navegación previo al login/registro."""
    if "next" in request.form or "next" in request.args:
        valor = request.form.get("next") if "next" in request.form else request.args.get("next")
        destino = destino_interno(valor)
        if destino:
            session["destino_acceso"] = destino
        else:
            session.pop("destino_acceso", None)
    return destino_interno(session.get("destino_acceso"))


def contexto_de_acceso(destino):
    #"""Genera el resumen visual de la función/película seleccionada previo al login."""
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
        "fecha": fecha_visible,
        "sala": funcion.get("sala_nombre", "Sala no disponible"),
        "precio": funcion.get("precio_base"),
        "butacas": butacas,
        "poster": poster_vista,
    }


def requiere_usuario(funcion):
    #"""Protege rutas que requieren estar autenticado."""
    @wraps(funcion)
    def vista(*args, **kwargs):
        if usuario_actual() is None:
            flash("Iniciá sesión para continuar.", "error")
            destino = destino_interno(request.full_path)
            if destino:
                session["destino_acceso"] = destino
            return redirect(url_for("auth.login", next=destino))
        return funcion(*args, **kwargs)
    return vista


def requiere_admin(funcion):
    #"""Protege rutas que requieren rol de Administrador."""
    @wraps(funcion)
    @requiere_usuario
    def vista(*args, **kwargs):
        if usuario_actual().get("rol", "").strip().casefold() != "administrador":
            abort(403)
        return funcion(*args, **kwargs)
    return vista