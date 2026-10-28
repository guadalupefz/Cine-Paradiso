from flask import Flask
from flask_cors import CORS
from src.routes.butacas import mis_rutas


app = Flask(__name__)

# Habilitar CORS para que el frontend pueda consumir la API
CORS(app) 

app.register_blueprint(mis_rutas, url_prefix='/api')


@app.route('/')
def index():
    return "Backend de Cine Paradiso"


if __name__ == '__main__':
    app.run("127.0.0.1", port=5000, debug=True)
