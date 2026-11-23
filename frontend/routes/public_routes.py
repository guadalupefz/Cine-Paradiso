from datetime import datetime
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, abort

from frontend.utils.api_client import llamar_backend, mensaje_error, lista
from frontend.utils.auth_helpers import usuario_actual
from frontend.utils.poster_helper import resolver_url_poster

public_bp = Blueprint("public", __name__)


@public_bp.get("/", endpoint="index")
def index():
    datos, estado = llamar_backend("GET", "/peliculas")
    peliculas, vistos = [], set()

    for peli in lista(datos, "peliculas"):
        if peli["id_pelicula"] not in vistos:
            peli["duracion"] = peli.get("duracion_minutos")
            peli["poster"] = resolver_url_poster(peli.get("poster"))
            peliculas.append(peli)
            vistos.add(peli["id_pelicula"])

    if estado != 200:
        flash(mensaje_error(datos), "error")

    return render_template(
        "cartelera.html",
        peliculas=peliculas,
        error=estado != 200
    )


@public_bp.get("/funciones", endpoint="ver_funciones")
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
            (p for p in catalogo if p.get("id_pelicula") == id_pelicula),
            {}
        )
        if not pelicula:
            pelicula = ficha.copy()
        elif ficha.get("poster"):
            pelicula["poster"] = ficha["poster"]

    if pelicula:
        pelicula["poster"] = resolver_url_poster(pelicula.get("poster"))

    # Formateo amigable de fechas y horarios para la vista
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    meses_cortos = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    meses_cortos2 = ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."]
    meses_largos = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    for funcion in funciones:
        try:
            fecha = datetime.strptime(
                funcion["fecha_hora_inicio"],
                "%a, %d %b %Y %H:%M:%S GMT"
            )
            funcion["mes_nombre"] = meses_largos[fecha.month - 1]
            funcion["anio"] = fecha.year
            funcion["fecha"] = f"{fecha.day} {meses_cortos[fecha.month - 1]}"
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


@public_bp.route("/peliculas/<int:id_pelicula>/resenas", methods=["GET", "POST"], endpoint="ver_resenas_pelicula")
def ver_resenas_pelicula(id_pelicula):
    ruta_resenas = f"/peliculas/{id_pelicula}/resenas"

    if request.method == "POST":
        usuario = usuario_actual()
        if usuario is None:
            flash("Iniciá sesión para publicar una reseña.", "error")
            destino = url_for('public.ver_resenas_pelicula', id_pelicula=id_pelicula)
            session["destino_acceso"] = destino
            return redirect(url_for('auth.login', next=destino))

        if usuario.get("rol", "").strip().casefold() != "cliente":
            abort(403)

        try:
            puntuacion = int(request.form.get("puntuacion", ""))
        except (TypeError, ValueError):
            puntuacion = None

        resultado, estado = llamar_backend(
            "POST",
            ruta_resenas,
            json={
                "puntuacion": puntuacion,
                "comentario": request.form.get("comentario", ""),
            },
        )
        if estado == 200:
            flash(mensaje_error(resultado), "ok")
        else:
            flash(mensaje_error(resultado), "error")
        return redirect(url_for('public.ver_resenas_pelicula', id_pelicula=id_pelicula))

    datos, estado = llamar_backend("GET", ruta_resenas)
    if estado == 404:
        abort(404)

    propia = None
    error_propio = None
    usuario = usuario_actual()
    if usuario and usuario.get("rol", "").strip().casefold() == "cliente":
        propia, estado_propio = llamar_backend("GET", ruta_resenas + "/propia")
        if estado_propio != 200:
            error_propio = mensaje_error(propia)
            propia = None

    return render_template(
        "resenas.html",
        datos=datos if estado == 200 else {},
        error_resenas=mensaje_error(datos) if estado != 200 else None,
        propia=propia,
        error_propio=error_propio,
    ), 200 if estado == 200 else estado