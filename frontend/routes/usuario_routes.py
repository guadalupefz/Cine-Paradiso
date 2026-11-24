import requests
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, abort, Response, send_file

from frontend.utils.api_client import llamar_backend, mensaje_error, lista, BACKEND_URL
from frontend.utils.auth_helpers import requiere_usuario, usuario_actual
from frontend.utils.pdf_service import crear_comprobante_pdf

usuario_bp = Blueprint("usuario", __name__)


@usuario_bp.get("/mis-compras", endpoint="mis_compras")
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

def consultar_comprobante(id_compra):
    """Consulta los datos del comprobante desde la API del backend."""
    comprobante, estado = llamar_backend(
        "GET",
        f"/compras/{id_compra}/comprobante"
    )

    if estado != 200:
        abort(estado)

    return comprobante


def obtener_comprobante(id_compra):
    """Obtiene el comprobante y verifica que la compra esté aprobada o confirmada."""
    comprobante = consultar_comprobante(id_compra)
    compra = comprobante["compra"]

    if compra["estado"].lower() not in ("aprobada", "confirmada"):
        abort(403)

    return comprobante

@usuario_bp.get("/mis-entradas", endpoint="mis_entradas")
@requiere_usuario
def mis_entradas():
    datos, estado = llamar_backend("GET", "/compras")
    compras = lista(datos, "compras") if estado == 200 else []

    return render_template(
        "entradas.html",
        compras=compras,
        usuario=usuario_actual(),
        error=estado != 200
    )


@usuario_bp.post("/mis-compras/<int:id_compra>/cancelar", endpoint="cancelar_compra_frontend")
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

    return redirect(url_for('usuario.mis_compras'))


@usuario_bp.get("/entradas/<int:id_entrada>/qr", endpoint="ver_qr_cliente")
@requiere_usuario
def ver_qr_cliente(id_entrada):
    headers = {}
    if session.get("backend_token"):
        headers["Authorization"] = "Bearer " + session["backend_token"]

    respuesta = requests.get(
        f"{BACKEND_URL}/qr/{id_entrada}",
        headers=headers,
        timeout=10
    )

    if respuesta.status_code != 200:
        abort(respuesta.status_code)

    return Response(respuesta.content, mimetype="image/png")


@usuario_bp.get("/compras/<int:id_compra>/comprobante", endpoint="ver_comprobante")
@requiere_usuario
def ver_comprobante(id_compra):
    comprobante = consultar_comprobante(id_compra)
    return render_template("comprobante.html", comprobante=comprobante)


@usuario_bp.get("/compras/<int:id_compra>/comprobante/pdf", endpoint="descargar_comprobante_pdf")
@requiere_usuario
def descargar_comprobante_pdf(id_compra):
    comprobante = obtener_comprobante(id_compra)

    compra = comprobante["compra"]
    entradas = comprobante["entradas"]
    servicios = comprobante.get("servicios", [])

    buffer = crear_comprobante_pdf(
        compra,
        entradas,
        servicios,
        session.get("backend_token")
    )

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"comprobante_{id_compra}.pdf"
    )