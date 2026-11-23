import secrets
from flask import Blueprint, render_template, request, session, redirect, url_for, flash

from frontend.utils.api_client import llamar_backend, mensaje_error
from frontend.utils.auth_helpers import destino_de_acceso, contexto_de_acceso

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/registro", methods=["GET", "POST"], endpoint="registro")
def registro():
    destino = destino_de_acceso()
    datos_formulario = {
        campo: request.form.get(campo, "")
        for campo in ("nombre", "apellido", "email")
    }
    error_formulario = None
    estado_pagina = 200

    if request.method == "POST":
        password = request.form.get("password", "")
        if password != request.form.get("confirmar_password", ""):
            error_formulario = "Las contraseñas no coinciden. Volvé a ingresarlas."
            estado_pagina = 400
        else:
            resultado, estado = llamar_backend(
                "POST",
                "/auth/registro",
                json={**datos_formulario, "password": password}
            )
            if estado == 201:
                session["email_acceso"] = datos_formulario["email"].strip().lower()
                flash("Tu cuenta fue creada. Iniciá sesión para continuar.", "ok")
                return redirect(url_for('auth.login', next=destino))

            error_formulario = mensaje_error(resultado)
            estado_pagina = estado

    return render_template(
        "registro.html",
        datos_formulario=datos_formulario,
        error_formulario=error_formulario,
        destino=destino,
        contexto=contexto_de_acceso(destino),
    ), estado_pagina


@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    destino = destino_de_acceso()
    email_acceso = (
        request.form.get("email", "")
        if request.method == "POST"
        else session.pop("email_acceso", "")
    )

    if request.method == "POST":
        datos, estado = llamar_backend(
            "POST",
            "/auth/login",
            json={
                "email": request.form.get("email", ""),
                "password": request.form.get("password", "")
            }
        )
        if estado == 200:
            session.clear()
            session["csrf_token"] = secrets.token_hex(24)
            session["backend_token"] = datos["access_token"]
            flash("Sesión iniciada.", "ok")
            usuario = datos.get("usuario", {})

            # Redirección inteligente según rol o navegación previa
            destino_final = destino or url_for(
                "admin.admin_resumen"
                if usuario.get("rol", "").strip().casefold() == "administrador"
                else "public.index"
            )
            return redirect(destino_final)

        flash(mensaje_error(datos), "error")

    return render_template(
        "login.html",
        destino=destino,
        email_acceso=email_acceso,
        contexto=contexto_de_acceso(destino)
    )


@auth_bp.post("/logout", endpoint="logout")
def logout():
    datos, estado = llamar_backend("POST", "/auth/logout")
    if estado not in (200, 401):
        flash("No se pudo cerrar la sesión en el servidor. Intentá nuevamente.", "error")
        return redirect(url_for('public.index'))

    session.clear()
    return redirect(url_for('public.index'))