import os

from dotenv import load_dotenv
from flask import Flask

from src.routes.butacas import mis_rutas
from src.routes.auth import auth_routes


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY no esta configurada. Definila en una variable de entorno."
    )

app.register_blueprint(mis_rutas, url_prefix='/api')
app.register_blueprint(auth_routes, url_prefix='/api')


@app.route('/')
def index():
    return "Backend de Cine Paradiso"


if __name__ == '__main__':
    app.run("127.0.0.1", port=5001, debug=True)
