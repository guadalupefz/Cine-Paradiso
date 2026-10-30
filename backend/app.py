from flask import Flask
from src.routes.butacas import mis_rutas
from src.routes.estadisticas import rutas_estadisticas
from src.routes.auth_routes import auth_bp

app = Flask(__name__)

app.register_blueprint(mis_rutas, url_prefix='/api')
app.register_blueprint(rutas_estadisticas, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')


@app.route('/')
def index():
    return "Backend de Cine Paradiso"


if __name__ == '__main__':
    app.run("127.0.0.1", port=5001, debug=True)
