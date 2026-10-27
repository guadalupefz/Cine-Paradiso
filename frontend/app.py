from flask import Flask, render_template

BACKEND_URL = "http://localhost:5001/api"

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("cartelera.html", peliculas=[])


if __name__ == "__main__":
    app.run(port=8080, debug=True)

