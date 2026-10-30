from flask import Flask, render_template, request

BACKEND_URL = "http://localhost:5001/api"

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("cartelera.html", peliculas=[])


@app.route("/funciones")
def ver_funciones():
    id_pelicula = request.args.get("id_pelicula", type=int)

    pelicula = {"titulo": "Nombre de la película"}
    funciones = []
    error = False

    return render_template(
        "funciones.html",
        pelicula=pelicula,
        funciones=funciones,
        error=error,
        id_pelicula=id_pelicula
    )


@app.route("/butacas/<int:id_funcion>")
def ver_butacas(id_funcion):
    pelicula = {"titulo": "Nombre de la película"}
    butacas = []
    error = False

    return render_template(
        "butacas.html",
        pelicula=pelicula,
        butacas=butacas,
        error=error,
        id_funcion=id_funcion
    )


@app.route("/compra")
def ver_compra():
    id_funcion = request.args.get("id_funcion", type=int)
    numeros_butacas = request.args.get("butacas", "")

    butacas_seleccionadas = [
        numero.strip()
        for numero in numeros_butacas.split(",")
        if numero.strip()
    ]

    error = not id_funcion or not butacas_seleccionadas

    return render_template(
        "compra.html",
        id_funcion=id_funcion,
        butacas=butacas_seleccionadas,
        error=error
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
