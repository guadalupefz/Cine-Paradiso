import os
import sys
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from flask import Flask

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
load_dotenv(RAIZ / ".env")

from backend.src.routes.auth_routes import auth_bp
from backend.src.routes.butacas import mis_rutas
from backend.src.routes.peliculas import peliculas_bp as peliculas_externas_bp
from backend.src.routes.peliculas_routes import peliculas_bp
from backend.src.routes.funciones_routes import funciones_bp
from backend.src.routes.locales_routes import locales_bp
from backend.src.routes.salas_routes import salas_bp
from backend.src.routes.compras_routes import compras_bp
from backend.src.routes.servicios_routes import servicios_bp
from backend.src.routes.estadisticas_routes import estadisticas_bp
from backend.src.routes.qr_routes import qr_bp
from backend.src.routes.reservas_routes import reservas_bp
from backend.src.services.correo_service import mail


app = Flask(__name__, static_folder="static")
app.config.update(
    SECRET_KEY=os.environ["SECRET_KEY"],
    SESSION_COOKIE_NAME="cine_backend",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
    MAX_CONTENT_LENGTH=1024 * 1024,
)

app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True") == "True"
app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL", "False") == "True"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

mail.init_app(app)

for blueprint in (auth_bp, mis_rutas, peliculas_externas_bp, peliculas_bp, funciones_bp, locales_bp, salas_bp, compras_bp, servicios_bp, estadisticas_bp, qr_bp, reservas_bp):
    app.register_blueprint(blueprint, url_prefix="/api")

@app.get("/")
def index():
    return "Backend de Cine Paradiso"

if __name__ == "__main__":
    app.run("127.0.0.1", port=5001, debug=os.environ.get("FLASK_DEBUG") == "1")
