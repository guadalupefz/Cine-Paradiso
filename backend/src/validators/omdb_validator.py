import re

def validar_busqueda_omdb(titulo):
    if not isinstance(titulo, str) or not titulo.strip():
        return "El título de búsqueda es obligatorio."

    titulo = titulo.strip()

    if len(titulo) > 150:
        return "El título no puede superar los 150 caracteres."

    if not re.search(r"[a-zA-Z0-9]", titulo):
        return "El título debe contener letras o números."

    return None

def validar_detalle_omdb(imdb_id):
    if not isinstance(imdb_id, str) or not imdb_id.strip():
        return "El IMDb ID es obligatorio."

    imdb_id = imdb_id.strip()

    if not re.fullmatch(r"tt\d{7,10}", imdb_id):
        return "El IMDb ID no tiene un formato válido."

    return None

def validar_importacion_omdb(datos):
    if not isinstance(datos, dict):
        return "Se esperaba un objeto JSON."

    imdb_id = datos.get("imdb_id")

    error = validar_detalle_omdb(imdb_id)

    if error:
        return error

    return None
