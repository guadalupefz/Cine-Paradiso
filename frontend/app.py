from flask import Flask, render_template, request

BACKEND_URL = "http://localhost:5001/api"

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("cartelera.html", peliculas=[])


@app.route("/funciones")
def ver_funciones():
    pelicula = {"titulo": "Nombre de la película"}
    funciones = []
    error = False

    return render_template(
        "funciones.html",
        pelicula=pelicula,
        funciones=funciones,
        error=error
    )


@app.route("/butacas/<int:id_funcion>")
def ver_butacas(id_funcion):
    id_pelicula = request.args.get("id_pelicula", type=int)
    pelicula = {"titulo": "Nombre de la película"}
    butacas = []
    error = False

    return render_template(
        "butacas.html",
        pelicula=pelicula,
        butacas=butacas,
        error=error,
        id_funcion=id_funcion,
        id_pelicula=id_pelicula
    )

@app.route("/servicios")
def ver_servicios():
    servicios = []
    error = False

    return render_template(
        "servicios.html",
        servicios=servicios,
        error=error
    )


if __name__ == "__main__":
    app.run(port=8080, debug=True)


