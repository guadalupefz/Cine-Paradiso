def crear_error(codigo, mensaje):
    return [{
        'code': codigo,
        'message': mensaje,
        'level': 'error'
    }]


def validar_datos_compra(data):

    if not isinstance(data, dict):
        return False, crear_error(
            'DATOS_INVALIDOS',
            'Los datos de la compra deben tener un formato válido.'
        )

    id_funcion = data.get("id_funcion")
    ids_butacas = data.get("ids_butacas")

    if not isinstance(id_funcion, int) or isinstance(id_funcion, bool) or id_funcion <= 0:
        return False, crear_error(
            'ID_FUNCION_INVALIDO',
            'El ID de la función debe ser un número positivo.'
        )

    if not isinstance(ids_butacas, list) or not ids_butacas:
        return False, crear_error(
            'BUTACAS_REQUERIDAS',
            'Debe seleccionar al menos una butaca.'
        )

    if any(
        not isinstance(id_butaca, int)
        or isinstance(id_butaca, bool)
        or id_butaca <= 0
        for id_butaca in ids_butacas
    ):
        return False, crear_error(
            'ID_BUTACA_INVALIDO',
            'Los IDs de las butacas deben ser números positivos.'
        )

    if len(ids_butacas) != len(set(ids_butacas)):
        return False, crear_error(
            'BUTACAS_REPETIDAS',
            'No se pueden seleccionar butacas repetidas.'
        )

    return True, None