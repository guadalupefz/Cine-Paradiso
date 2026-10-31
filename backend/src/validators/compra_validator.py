
def validar_datos_compra(data):
    if not isinstance(data, dict):
        return False, "Los datos de la compra deben tener un formato válido."

    id_funcion = data.get("id_funcion")
    ids_butacas = data.get("ids_butacas")

    if not isinstance(id_funcion, int) or isinstance(id_funcion, bool) or id_funcion <= 0:
        return False, "El ID de la función debe ser un número positivo."

    if not isinstance(ids_butacas, list) or not ids_butacas:
        return False, "Debe seleccionar al menos una butaca."

    if any(
        not isinstance(id_butaca, int)
        or isinstance(id_butaca, bool)
        or id_butaca <= 0
        for id_butaca in ids_butacas
    ):
        return False, "Los IDs de las butacas deben ser números positivos."

    if len(ids_butacas) != len(set(ids_butacas)):
        return False, "No se pueden seleccionar butacas repetidas."

    return True, None
