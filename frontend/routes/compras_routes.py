import os
from datetime import datetime
from flask import Blueprint, render_template, request, session, redirect, url_for, flash

from frontend.utils.api_client import llamar_backend, mensaje_error, lista, BACKEND_ORIGEN
from frontend.utils.auth_helpers import requiere_usuario, usuario_actual, destino_interno
from frontend.utils.poster_helper import resolver_url_poster, obtener_servicios_seleccionados

compras_bp = Blueprint("compras", __name__)


def pago_aprobado():
    #"""Simulador interno de pasarela de pago."""
    return os.environ.get("SIMULAR_PAGO_RECHAZADO") != "1"


@compras_bp.get("/butacas/<int:id_funcion>", endpoint="ver_butacas")
@requiere_usuario
def ver_butacas(id_funcion):
    datos_butacas, estado_butacas = llamar_backend("GET", f"/funciones/{id_funcion}/butacas")
    butacas = lista(datos_butacas, "butacas")

    datos_cartelera, estado_cartelera = llamar_backend("GET", "/cartelera")
    funciones_cartelera = lista(datos_cartelera, "cartelera")

    funcion = next(
        (f for f in funciones_cartelera if f.get("id_funcion") == id_funcion),
        None
    )

    if funcion:
        funcion["poster"] = resolver_url_poster(funcion.get("poster"))
        try:
            fecha = datetime.strptime(funcion["fecha_hora_inicio"], "%a, %d %b %Y %H:%M:%S GMT")
            dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
            meses_cortos = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
            
            dia_semana = dias[fecha.weekday()].capitalize()
            mes = meses_cortos[fecha.month - 1]
            funcion["fecha"] = f"{dia_semana} {fecha.day} {mes}, {fecha.year}"
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
        error=(estado_butacas != 200 or estado_cartelera != 200 or funcion is None)
    )


@compras_bp.route("/servicios", methods=["GET", "POST"], endpoint="ver_servicios")
def ver_servicios():
    id_funcion = request.values.get("id_funcion", type=int)
    bruto_butacas = request.values.get("butacas", "")

    if isinstance(bruto_butacas, str):
        ids_butacas = [b.strip() for b in bruto_butacas.split(",") if b.strip()]
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
        return redirect(url_for("auth.login", next=destino))

    if not id_funcion or not ids_butacas:
        return redirect(url_for("public.ver_funciones"))

    datos_cartelera, estado_cartelera = llamar_backend("GET", "/cartelera")
    funciones = lista(datos_cartelera, "cartelera")
    funcion = next((f for f in funciones if f.get("id_funcion") == id_funcion), None)

    if not funcion:
        flash("No encontramos la función solicitada.", "error")
        return redirect(url_for("public.ver_funciones"))

    funcion["poster"] = resolver_url_poster(funcion.get("poster"))

    return render_template(
        "servicios.html",
        servicios=servicios,
        funcion=funcion,
        id_funcion=id_funcion,
        ids_butacas=ids_butacas,
        detalle_butacas=ids_butacas,
        servicios_seleccionados=[],
        modo_catalogo=False,
        error=estado != 200
    )


@compras_bp.get("/compra", endpoint="ver_compra")
@requiere_usuario
def ver_compra():
    id_funcion = request.args.get("id_funcion", type=int)
    ids_butacas = [b.strip() for b in request.args.get("butacas", "").split(",") if b.strip()]

    if not id_funcion or id_funcion <= 0 or not ids_butacas:
        return render_template("compra.html", error=True, id_funcion=id_funcion, butacas=ids_butacas)

    servicios_texto = request.args.get("servicios", "")
    try:
        servicios_seleccionados = obtener_servicios_seleccionados(servicios_texto)
    except ValueError:
        flash("La selección de servicios no es válida", "error")
        return redirect(url_for('compras.ver_servicios', id_funcion=id_funcion, butacas=",".join(ids_butacas)))

    datos_cartelera, estado_cartelera = llamar_backend("GET", "/cartelera")
    funciones = lista(datos_cartelera, "cartelera")
    funcion = next((f for f in funciones if f.get("id_funcion") == id_funcion), None)

    if estado_cartelera != 200 or not funcion:
        return render_template("compra.html", error=True, id_funcion=id_funcion, butacas=ids_butacas)

    funcion["poster"] = resolver_url_poster(funcion.get("poster"))

    # Gestión de vigencia de la reserva
    vencimiento_reserva = None
    reserva_vencida = False
    reserva_pendiente = session.get("reserva_pendiente")

    if reserva_pendiente and reserva_pendiente.get("id_funcion") == id_funcion:
        vencimiento_texto = reserva_pendiente.get("fecha_hora_vencimiento")
        if vencimiento_texto:
            try:
                vencimiento_reserva = datetime.strptime(vencimiento_texto, "%Y-%m-%d %H:%M:%S")
                if datetime.now() >= vencimiento_reserva:
                    reserva_vencida = True
                    session.pop("reserva_pendiente", None)
            except (TypeError, ValueError):
                pass

    return render_template(
        "compra.html",
        funcion=funcion,
        id_funcion=id_funcion,
        butacas=ids_butacas,
        servicios=servicios_seleccionados,
        error=False,
        vencimiento_reserva=vencimiento_reserva,
        reserva_vencida=reserva_vencida
    )


@compras_bp.post("/reservar-compra", endpoint="reservar_compra")
@requiere_usuario
def reservar_compra():
    id_funcion = request.form.get("id_funcion", type=int)
    butacas_texto = request.form.get("butacas", "")
    servicios_texto = request.form.get("servicios", "")

    if not id_funcion or id_funcion <= 0:
        flash("La función seleccionada no es válida.", "error")
        return redirect(url_for("public.index"))

    try:
        ids_butacas = [int(v.strip()) for v in butacas_texto.split(",") if v.strip()]
        servicios = obtener_servicios_seleccionados(servicios_texto)
    except ValueError:
        flash("La selección de compra no es válida", "error")
        return redirect(url_for('compras.ver_butacas', id_funcion=id_funcion))

    if not ids_butacas or any(b <= 0 for b in ids_butacas) or len(ids_butacas) != len(set(ids_butacas)):
        flash("La selección de butacas no es válida", "error")
        return redirect(url_for('compras.ver_butacas', id_funcion=id_funcion))

    reserva_actual = session.get("reserva_pendiente")

    if reserva_actual:
        compras, estado = llamar_backend("GET", "/compras")
        if estado != 200:
            flash("No se pudo verificar tu reserva pendiente", "error")
            return redirect(url_for("usuario.mis_compras"))

        compra_guardada = next((c for c in lista(compras, "compras") if c.get("id_compra") == reserva_actual["id_compra"]), None)

        if compra_guardada and compra_guardada["estado"] in ("confirmada", "aprobada"):
            session.pop("reserva_pendiente", None)
            return redirect(url_for("usuario.ver_comprobante", id_compra=reserva_actual["id_compra"]))

        if not compra_guardada or compra_guardada["estado"] in ("expirada", "rechazada", "cancelada"):
            session.pop("reserva_pendiente", None)
            reserva_actual = None
        elif compra_guardada["estado"] == "pendiente":
            vencimiento_texto = reserva_actual.get("fecha_hora_vencimiento")
            if vencimiento_texto:
                try:
                    vencimiento = datetime.strptime(vencimiento_texto, "%Y-%m-%d %H:%M:%S")
                    if datetime.now() >= vencimiento:
                        session.pop("reserva_pendiente", None)
                        reserva_actual = None
                except (TypeError, ValueError):
                    flash("No se pudo verificar el vencimiento de la reserva", "error")
                    return redirect(url_for("usuario.mis_compras"))

    if reserva_actual:
        if reserva_actual["id_funcion"] != id_funcion:
            flash("Ya tenés una reserva pendiente para otra función", "error")
            return redirect(url_for("usuario.mis_compras"))

        cambio_butacas = reserva_actual["butacas"] != ids_butacas
        cambio_servicios = reserva_actual.get("servicios", []) != servicios

        if cambio_butacas or cambio_servicios:
            resultado, estado = llamar_backend("PUT", f"/reservas/{reserva_actual['id_compra']}", json={"butacas": ids_butacas, "servicios": servicios})
            if estado != 200:
                flash("No se pudo modificar la reserva: " + mensaje_error(resultado), "error")
                return redirect(url_for("usuario.mis_compras"))

            reserva_actual.update({
                "butacas": ids_butacas,
                "servicios": servicios,
                "fecha_hora_vencimiento": resultado.get("fecha_hora_vencimiento", reserva_actual.get("fecha_hora_vencimiento"))
            })
            session["reserva_pendiente"] = reserva_actual
    else:
        resultado, estado = llamar_backend("POST", "/reservas", json={"id_funcion": id_funcion, "butacas": ids_butacas, "servicios": servicios})
        if estado != 201:
            flash("No se pudo iniciar la reserva: " + mensaje_error(resultado), "error")
            return redirect(url_for('compras.ver_butacas', id_funcion=id_funcion))

        session["reserva_pendiente"] = {
            "id_compra": resultado["id_compra"],
            "id_funcion": id_funcion,
            "butacas": ids_butacas,
            "servicios": servicios,
            "fecha_hora_vencimiento": resultado.get("fecha_hora_vencimiento")
        }

    params = {"id_funcion": id_funcion, "butacas": ",".join(str(b) for b in ids_butacas)}
    if servicios_texto:
        params["servicios"] = servicios_texto

    return redirect(url_for('compras.ver_compra', **params))


@compras_bp.post("/procesar-compra", endpoint="procesar_compra")
@requiere_usuario
def procesar_compra():
    id_funcion = request.form.get("id_funcion", type=int)
    butacas_texto = request.form.get("butacas", "")

    if not id_funcion or id_funcion <= 0:
        flash("La función seleccionada no es válida.", "error")
        return redirect(url_for("public.index"))

    try:
        ids_butacas = [int(b.strip()) for b in butacas_texto.split(",") if b.strip()]
    except ValueError:
        flash("La selección de butacas no es válida.", "error")
        return redirect(url_for('compras.ver_butacas', id_funcion=id_funcion))

    servicios_texto = request.form.get("servicios", "")
    try:
        servicios_seleccionados = obtener_servicios_seleccionados(servicios_texto)
    except ValueError:
        flash("La selección de servicios no es válida", "error")
        return redirect(url_for('compras.ver_servicios', id_funcion=id_funcion, butacas=butacas_texto))

    if request.form.get("metodo_pago") != "tarjeta":
        flash("Selecciona un método de pago valido", "error")
        return redirect(url_for('compras.ver_compra', id_funcion=id_funcion, butacas=butacas_texto))

    reserva_pendiente = session.get("reserva_pendiente")
    if not reserva_pendiente or not reserva_pendiente.get("id_compra"):
        flash("Primero tenés que reservar las butacas para continuar con el pago", "error")
        return redirect(url_for('compras.ver_servicios', id_funcion=id_funcion, butacas=butacas_texto))

    if not pago_aprobado():
        id_compra = reserva_pendiente["id_compra"]
        resultado, estado = llamar_backend("POST", f"/reservas/{id_compra}/rechazar")
        if estado != 200:
            flash("El pago fue rechazado, pero no se pudo liberar la reserva: " + mensaje_error(resultado), "error")
            return redirect(url_for("usuario.mis_compras"))

        session.pop("reserva_pendiente", None)
        flash("El pago fue rechazado. Seleccioná nuevamente tus servicios y reintentá", "error")
        return redirect(url_for('compras.ver_servicios', id_funcion=id_funcion, butacas=butacas_texto))

    id_compra = reserva_pendiente["id_compra"]
    resultado, estado = llamar_backend("POST", f"/compras/{id_compra}/confirmar")

    if estado == 200:
        session.pop("reserva_pendiente", None)
        datos_compra = resultado.get("compra", resultado)
        mensaje_correo = datos_compra.get("mensaje_correo")
        if mensaje_correo:
            flash(mensaje_correo, "ok")
        else:
            flash("La compra fue confirmada. Podés consultar tus entradas desde el comprobante.", "ok")

        return redirect(url_for("usuario.ver_comprobante", id_compra=id_compra))

    flash("No se pudo confirmar la compra: " + mensaje_error(resultado), "error")
    return redirect(url_for('compras.ver_compra', id_funcion=id_funcion, butacas=butacas_texto))