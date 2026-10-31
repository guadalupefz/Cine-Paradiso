from flask import Flask

from backend.src.routes.butacas import mis_rutas
from backend.src.routes.auth_routes import auth_bp
from backend.src.routes.peliculas_routes import peliculas_bp
from backend.src.routes.funciones_routes import funciones_bp
from backend.src.routes.locales_routes import locales_bp
from backend.src.routes.salas_routes import salas_bp
from backend.src.routes.compras_routes import compras_bp

app = Flask(__name__)

app.register_blueprint(mis_rutas, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(peliculas_bp, url_prefix='/api')
app.register_blueprint(funciones_bp, url_prefix='/api')
app.register_blueprint(locales_bp, url_prefix='/api')
app.register_blueprint(salas_bp, url_prefix='/api')
app.register_blueprint(compras_bp, url_prefix='/api')


@app.route('/')
def index():
    return "Backend de Cine Paradiso"


if __name__ == '__main__':
    app.run("127.0.0.1", port=5001, debug=True)
