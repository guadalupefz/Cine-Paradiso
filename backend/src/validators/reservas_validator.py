def validar_datos_reserva(id_funcion: int, data: dict):

    # Valida los datos de entrada para la creación de una reserva.
    # Retorna una lista de diccionarios de error acumulativos.

    errores = []

    # 1. Validar ID de la función (parámetro de URL)
    if isinstance(id_funcion, bool) or not isinstance(id_funcion, int) or id_funcion <= 0:
        errores.append({
            "code": "ID_FUNCION_INVALIDO",
            "message": "El ID de la función debe ser un número entero positivo.",
            "field": "id_funcion"
        })

    # 2. Validar que el cuerpo sea un diccionario/JSON
    if not isinstance(data, dict):
        errores.append({
            "code": "JSON_INVALIDO",
            "message": "Se requiere un cuerpo JSON válido."
        })
        return errores

    # 3. Validar id_usuario
    if "id_usuario" not in data:
        errores.append({
            "code": "CAMPO_REQUERIDO",
            "message": "El campo 'id_usuario' es obligatorio.",
            "field": "id_usuario"
        })
    else:
        id_user = data["id_usuario"]
        if isinstance(id_user, bool) or not isinstance(id_user, int) or id_user <= 0:
            errores.append({
                "code": "ID_USUARIO_INVALIDO",
                "message": "El ID de usuario debe ser un entero positivo.",
                "field": "id_usuario"
            })

    # 4. Validar lista de butacas
    if "butacas" not in data:
        errores.append({
            "code": "CAMPO_REQUERIDO",
            "message": "El campo 'butacas' es obligatorio.",
            "field": "butacas"
        })
    else:
        butacas = data["butacas"]
        if not isinstance(butacas, list) or len(butacas) == 0:
            errores.append({
                "code": "BUTACAS_INVALIDAS",
                "message": "El campo 'butacas' debe ser una lista no vacía de IDs.",
                "field": "butacas"
            })
        else:
            for idx, id_b in enumerate(butacas):
                if isinstance(id_b, bool) or not isinstance(id_b, int) or id_b <= 0:
                    errores.append({
                        "code": "BUTACA_ID_INVALIDO",
                        "message": f"El ID de butaca en posición {idx} debe ser un entero positivo.",
                        "field": f"butacas[{idx}]"
                    })
    
    return errores