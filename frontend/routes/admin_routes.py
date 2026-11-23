from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_file

from frontend.utils.api_client import llamar_backend, mensaje_error, lista
from frontend.utils.auth_helpers import requiere_admin
from frontend.utils.poster_helper import resolver_url_poster
from frontend.utils.pdf_service import crear_informe_estadisticas_pdf

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/admin", endpoint="admin_resumen")
@requiere_admin
def admin_resumen():
    desde = request.args.get("desde", "")
    hasta = request.args.get("hasta", "")
    id_local = request.args.get("id_local", type=int)

    params = {}
    if desde:
        params["desde"] = desde
    if hasta:
        params["hasta"] = hasta
    if id_local:
        params["id_local"] = id_local

    ventas, ev = llamar_backend("GET", "/estadisticas/ventas", params=params)
    ocupacion, eo = llamar_backend("GET", "/estadisticas/ocupacion", params=params)

    datos_locales, estado_locales = llamar_backend("GET", "/locales")
    locales = lista(datos_locales, "locales") if estado_locales == 200 else []

    return render_template(
        "admin/resumen_admin.html",
        ventas=ventas if ev == 200 else {},
        ocupacion=ocupacion if eo == 200 else {},
        ventas_ok=ev == 200,
        ocupacion_ok=eo == 200,
        locales=locales,
        filtros={
            "desde": desde,
            "hasta": hasta,
            "id_local": id_local
        }
    )


@admin_bp.get("/admin/estadisticas/pdf", endpoint="descargar_informe_estadisticas")
@requiere_admin
def descargar_informe_estadisticas():
    ventas, estado_ventas = llamar_backend("GET", "/estadisticas/ventas")
    ocupacion, estado_ocupacion = llamar_backend("GET", "/estadisticas/ocupacion")

    if estado_ventas != 200 or estado_ocupacion != 200:
        error = (
            mensaje_error(ventas) if estado_ventas != 200
            else mensaje_error(ocupacion)
        )
        flash(f"No se pudo generar el informe: {error}", "error")
        return redirect(url_for('admin.admin_resumen'))

    archivo = crear_informe_estadisticas_pdf(ventas, ocupacion)
    nombre = f"informe_ventas_rendimiento_{datetime.now():%Y%m%d}.pdf"

    return send_file(
        archivo,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nombre,
    )


@admin_bp.route("/admin/servicios", methods=["GET", "POST"], endpoint="admin_servicios")
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
            return redirect(url_for('admin.admin_servicios'))

        if accion == "eliminar":
            flash(mensaje_error(resultado), "error")
            return redirect(url_for('admin.admin_servicios'))

        error_formulario = mensaje_error(resultado)
        estado_formulario = estado
        if accion == "editar":
            servicio_editar = {"id_servicio": identificador}

    datos, estado = llamar_backend("GET", "/servicios")
    error_listado = estado != 200
    servicios = lista(datos, "servicios") if not error_listado else []

    if request.method == "GET" and "editar" in request.args:
        editar = request.args.get("editar", type=int)
        if editar and not error_listado:
            servicio_editar = next((s for s in servicios if s["id_servicio"] == editar), None)
            if servicio_editar:
                datos_formulario = {
                    "nombre": servicio_editar.get("nombre", ""),
                    "descripcion": servicio_editar.get("descripcion", ""),
                    "precio": str(servicio_editar.get("precio", "")),
                }

    return render_template(
        "admin/servicios_admin.html",
        servicios=servicios,
        servicio_editar=servicio_editar,
        datos_formulario=datos_formulario,
        error_formulario=error_formulario,
        error_listado=error_listado,
    ), estado_formulario


@admin_bp.route("/admin/peliculas", methods=["GET", "POST"], endpoint="admin_peliculas")
@requiere_admin
def admin_peliculas():
    campos = ("titulo", "sinopsis", "poster", "clasificacion", "genero", "duracion_minutos")
    datos_formulario = {campo: "" for campo in campos}
    datos_formulario["poster"] = "/static/img/default.svg"

    pelicula_editar = None
    mostrar_formulario = request.args.get("nuevo") == "1"
    resultado_api = None
    busqueda_api = request.form.get("titulo_api", "").strip() if request.method == "POST" else ""
    error_api = None
    error_formulario = None
    estado_pagina = 200

    if request.method == "POST":
        accion = request.form.get("accion", "")

        if accion in ("buscar_api", "importar"):
            if not busqueda_api:
                error_api = "Ingresá un título para buscar la película."
                estado_pagina = 400
            else:
                metodo = "POST" if accion == "importar" else "GET"
                ruta = f"/peliculas/omdb/{'importar/' if accion == 'importar' else ''}{busqueda_api}"
                resultado, estado = llamar_backend(metodo, ruta)

                rechazo = next(
                    (str(v) for k, v in resultado.items() if k.strip().casefold() == "error"),
                    None
                ) if isinstance(resultado, dict) else None

                if estado not in (200, 201) or rechazo:
                    error_api = rechazo or mensaje_error(resultado)
                    estado_pagina = estado if estado not in (200, 201) else 409
                elif accion == "importar":
                    flash(mensaje_error(resultado), "ok")
                    return redirect(url_for('admin.admin_peliculas'))
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
                return redirect(url_for('admin.admin_peliculas'))

            error_formulario = mensaje_error(resultado)
            estado_pagina = estado
            if accion == "editar":
                pelicula_editar = {"id_pelicula": identificador}
        else:
            abort(400)

    datos, estado = llamar_backend("GET", "/peliculas")
    error_listado = estado != 200
    peliculas = lista(datos, "peliculas") if not error_listado else []

    if request.method == "GET" and "editar" in request.args:
        editar = request.args.get("editar", type=int)
        if editar and not error_listado:
            pelicula_editar = next((p for p in peliculas if p["id_pelicula"] == editar), None)
            if pelicula_editar:
                mostrar_formulario = True
                datos_formulario = {campo: pelicula_editar.get(campo) or "" for campo in campos}
                duracion = str(datos_formulario["duracion_minutos"]).strip().split()
                datos_formulario["duracion_minutos"] = duracion[0] if duracion else ""

    return render_template(
        "admin/peliculas_admin.html",
        peliculas=peliculas,
        pelicula_editar=pelicula_editar,
        mostrar_formulario=mostrar_formulario,
        datos_formulario=datos_formulario,
        resultado_api=resultado_api,
        busqueda_api=busqueda_api,
        error_api=error_api,
        error_formulario=error_formulario,
        error_listado=error_listado,
        poster_para_vista=resolver_url_poster,
    ), estado_pagina


@admin_bp.route("/admin/funciones", methods=["GET", "POST"], endpoint="admin_funciones")
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
            return redirect(url_for('admin.admin_funciones'))

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

    for local in locales:
        datos, estado = llamar_backend("GET", f"/locales/{local['id_local']}/salas")
        if estado == 200:
            for sala in lista(datos, "salas"):
                salas.append({**sala, "id_local": local["id_local"], "local_nombre": local["nombre"]})

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

    funciones.sort(key=lambda f: f["fecha_formulario"] or "9999")

    if request.method == "GET" and "editar" in request.args:
        editar = request.args.get("editar", type=int)
        if editar and ef == 200:
            funcion_editar = next((f for f in funciones if f["id_funcion"] == editar), None)
            if funcion_editar:
                mostrar_formulario = True
                datos_formulario = {
                    "id_pelicula": str(funcion_editar.get("id_pelicula", "")),
                    "id_sala": str(funcion_editar.get("id_sala", "")),
                    "fecha_hora_inicio": funcion_editar.get("fecha_formulario", ""),
                    "precio_base": str(funcion_editar.get("precio_base", "")),
                }

    return render_template(
        "admin/funciones_admin.html",
        funciones=funciones,
        peliculas=peliculas,
        locales=locales,
        salas=salas,
        funcion_editar=funcion_editar,
        mostrar_formulario=mostrar_formulario,
        datos_formulario=datos_formulario,
        error_formulario=error_formulario,
        error_listado=ef != 200,
    ), estado_pagina


@admin_bp.route("/admin/locales", methods=["GET", "POST"], endpoint="admin_locales")
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
            return redirect(url_for('admin.admin_locales'))
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


@admin_bp.post("/admin/locales/<int:id_local>/eliminar", endpoint="eliminar_local_admin")
@requiere_admin
def eliminar_local_admin(id_local):
    resultado, estado = llamar_backend("DELETE", f"/locales/{id_local}")
    flash(mensaje_error(resultado), "ok" if estado == 200 else "error")
    return redirect(url_for('admin.admin_locales'))


@admin_bp.post("/admin/salas/<int:id_sala>/eliminar", endpoint="eliminar_sala_admin")
@requiere_admin
def eliminar_sala_admin(id_sala):
    resultado, estado = llamar_backend("DELETE", f"/salas/{id_sala}")
    flash(mensaje_error(resultado), "ok" if estado == 200 else "error")
    return redirect(url_for('admin.admin_salas'))


@admin_bp.route("/admin/salas", methods=["GET", "POST"], endpoint="admin_salas")
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
                return redirect(url_for('admin.admin_salas', local=id_local))
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


@admin_bp.route("/admin/salas/<int:id_sala>/butacas", methods=["GET", "POST"], endpoint="admin_butacas")
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
        return redirect(url_for('admin.admin_salas'))

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
                return redirect(url_for('admin.admin_salas'))
            error_formulario = mensaje_error(resultado)

    return render_template(
        "admin/butacas_admin.html",
        sala=sala_seleccionada,
        distribucion=distribucion,
        error_formulario=error_formulario,
    )


@admin_bp.route("/admin/validar-qr", methods=["GET", "POST"], endpoint="validar_qr")
@requiere_admin
def validar_qr():
    resultado = None
    if request.method == "POST":
        resultado, estado = llamar_backend(
            "POST",
            "/qr/validar",
            json={
                "qr_token": request.form.get("qr_token", ""),
                "id_funcion": request.form.get("id_funcion", type=int)
            }
        )
        flash(mensaje_error(resultado), "ok" if estado == 200 else "error")

    return render_template("admin/validar_qr.html", resultado=resultado)