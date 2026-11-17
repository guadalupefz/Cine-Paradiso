def validar_datos_resena(datos):
    if not isinstance(datos, dict):
        return "Se esperaba un objeto JSON."

    puntuacion = datos.get("puntuacion")
    if type(puntuacion) is not int or not 1 <= puntuacion <= 5:
        return "La puntuación debe ser un número entero entre 1 y 5."

    comentario = datos.get("comentario", "")
    if not isinstance(comentario, str) or len(comentario.strip()) > 1000:
        return "El comentario debe tener como máximo 1000 caracteres."

    return None
