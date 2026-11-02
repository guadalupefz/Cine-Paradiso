def validar_datos_reserva(id_funcion: int, data: dict):

    errores = []

    if isinstance(id_funcion, bool) or not isinstance(id_funcion, int) or id_funcion <= 0:
        errores.append({
            "code": "ID_FUNCION_INVALIDO",
            "message": "El ID de la función debe ser un número entero positivo.",
            "field": "id_funcion"
        })

    if not isinstance(data, dict):
        errores.append({
            "code": "JSON_INVALIDO",
            "message": "Se requiere un cuerpo JSON válido."
        })
        return errores

    # Validar butacas
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
            if len(butacas) != len(set(butacas)):
                errores.append({
                    "code": "BUTACAS_REPETIDAS",
                    "message": "No se pueden seleccionar butacas repetidas.",
                    "field": "butacas"
                })

            for idx, id_b in enumerate(butacas):
                if isinstance(id_b, bool) or not isinstance(id_b, int) or id_b <= 0:
                    errores.append({
                        "code": "BUTACA_ID_INVALIDO",
                        "message": f"El ID de butaca en posición {idx} debe ser un entero positivo.",
                        "field": f"butacas[{idx}]"
                    })

    # Validar servicios adicionales
    servicios = data.get("servicios", [])

    if not isinstance(servicios, list):
        errores.append({
            "code": "SERVICIOS_INVALIDOS",
            "message": "El campo 'servicios' debe ser una lista.",
            "field": "servicios"
        })

    else:
        ids_servicios = []

        for idx, servicio in enumerate(servicios):

            if not isinstance(servicio, dict):
                errores.append({
                    "code": "SERVICIO_INVALIDO",
                    "message": "Cada servicio debe ser un objeto.",
                    "field": f"servicios[{idx}]"
                })
                continue

            id_servicio = servicio.get("id_servicio")
            cantidad = servicio.get("cantidad")

            if isinstance(id_servicio, bool) or not isinstance(id_servicio, int) or id_servicio <= 0:
                errores.append({
                    "code": "ID_SERVICIO_INVALIDO",
                    "message": "El ID del servicio debe ser un entero positivo.",
                    "field": f"servicios[{idx}].id_servicio"
                })
            else:
                ids_servicios.append(id_servicio)

            if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
                errores.append({
                    "code": "CANTIDAD_INVALIDA",
                    "message": "La cantidad debe ser un entero positivo.",
                    "field": f"servicios[{idx}].cantidad"
                })

        if len(ids_servicios) != len(set(ids_servicios)):
            errores.append({
                "code": "SERVICIOS_REPETIDOS",
                "message": "No se puede seleccionar el mismo servicio más de una vez. Se debe indicar su cantidad.",
                "field": "servicios"
            })

    return errores