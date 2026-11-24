def validar_datos_local(data):
    if not isinstance(data, dict):
        return "Se requiere un JSON válido."

    nombre = data.get("nombre")
    direccion = data.get("direccion")

    if not isinstance(nombre, str) or not nombre.strip() or len(nombre.strip()) > 100:
        return "El nombre es obligatorio y debe tener hasta 100 caracteres."

    if not isinstance(direccion, str) or not direccion.strip() or len(direccion.strip()) > 200:
        return "La dirección es obligatoria y debe tener hasta 200 caracteres."

    return None

def validar_id_local(id_local):
    if type(id_local) is not int or id_local <= 0:
        return "El ID del local debe ser positivo."

    return None