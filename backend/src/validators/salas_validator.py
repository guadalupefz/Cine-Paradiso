def validar_id_local(id_local):
    if id_local <= 0:
        return "El ID del local debe ser positivo."

    return None


def validar_datos_sala(data):
    if not isinstance(data, dict):
        return "Se requiere un JSON válido."

    nombre = data.get("nombre")
    capacidad = data.get("capacidad")

    if not isinstance(nombre, str) or not nombre.strip() or len(nombre.strip()) > 50:
        return "El nombre de la sala es obligatorio y debe tener hasta 50 caracteres."

    if type(capacidad) is not int or capacidad <= 0:
        return "La capacidad debe ser un entero positivo."

    return None

def validar_id_sala(id_sala):
    if id_sala <= 0:
        return "El ID de la sala debe ser positivo."

    return None
