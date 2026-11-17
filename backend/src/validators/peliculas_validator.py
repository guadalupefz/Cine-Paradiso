from backend.src.validators.duracion_validator import minutos_de_duracion


def validar_pelicula(datos):
    if not isinstance(datos, dict):
        return None, "Se esperaba un objeto JSON."

    campos = ("titulo", "sinopsis", "poster", "clasificacion", "genero")
    for campo in campos:
        valor = datos.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            return None, f"El campo {campo} es obligatorio."

    try:
        duracion = minutos_de_duracion(datos.get("duracion_minutos"))
    except ValueError as error:
        return None, str(error)

    return {
        "titulo": datos["titulo"].strip(),
        "sinopsis": datos["sinopsis"].strip(),
        "poster": datos["poster"].strip(),
        "clasificacion": datos["clasificacion"].strip(),
        "genero": datos["genero"].strip(),
        "duracion_minutos": duracion,
    }, None


def validar_id_pelicula(id_pelicula):
    if type(id_pelicula) is not int or id_pelicula <= 0:
        return "El ID de la película debe ser un entero positivo."
    return None
