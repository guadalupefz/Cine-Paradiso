import os
import secrets
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, abort, url_for
from frontend.utils.auth_helpers import usuario_actual

# Importación de Blueprints
from frontend.routes.auth_routes import auth_bp
from frontend.routes.public_routes import public_bp
from frontend.routes.compras_routes import compras_bp
from frontend.routes.usuario_routes import usuario_bp
from frontend.routes.admin_routes import admin_bp

# Carga de variables de entorno (.env)
RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

app = Flask(
    __name__,
    template_folder=str(Path(__file__).resolve().parent / "templates"),
    static_folder=str(Path(__file__).resolve().parent / "static")
)

# 1. Configuración de Sesiones y Archivos
app.config.update(
    SECRET_KEY=os.environ.get("FRONTEND_SECRET_KEY") or os.environ["SECRET_KEY"] + ":frontend",
    SESSION_COOKIE_NAME="cine_frontend",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
)

# 2. Controladores Globales CSRF y Contexto Jinja
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
    return {
        "usuario_actual": usuario_actual(),
        "csrf_token": session["csrf_token"]
    }

# 3. Manejadores Globales de Errores HTTP
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
        mensaje="La imagen o los datos enviados superan el límite de 5 MB. Elegí una imagen más liviana y volvé a intentarlo."
    ), 413

# 4. Registro de Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(public_bp)
app.register_blueprint(compras_bp)
app.register_blueprint(usuario_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    app.run(host=host, port=8080, debug=os.environ.get("FLASK_DEBUG") == "1")