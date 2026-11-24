def validar_pelicula(datos):
    if not isinstance(datos, dict):
        raise ValueError("Se esperaba un objeto JSON.")

    if not datos:
        raise ValueError("No se proporcionaron datos para la película.")

    resultado = {}

    # Validación de campos de texto y sus longitudes máximas.
    campos_texto = {
        "titulo": 150,
        "sinopsis": 65000,
        "poster": 100,
        "clasificacion": 20,
        "genero": 50
    }

    for campo, limite in campos_texto.items():
        valor = datos.get(campo)
        if not isinstance(valor, str):
            raise ValueError(
                f"El campo '{campo}' debe ser un texto."
            )

        valor = valor.strip()
        if not valor:
            raise ValueError(
                f"El campo '{campo}' es obligatorio."
            )

        if len(valor) > limite:
            raise ValueError(
                f"El campo '{campo}' no puede superar "
                f"los {limite} caracteres."
            )

        resultado[campo] = valor
      
    duracion = datos.get("duracion_minutos")
    if type(duracion) is not int:
        raise ValueError(
            "La duración debe ser un número entero."
        )

    if not 1 <= duracion <= 1440:
        raise ValueError(
            "La duración debe estar entre 1 y 1440 minutos."
        )

    resultado["duracion_minutos"] = duracion
    return resultado


def validar_id_pelicula(id_pelicula):
    """
    Valida el identificador de una película.
    """

    if type(id_pelicula) is not int or id_pelicula <= 0:
        raise ValueError(
            "El ID de la película debe ser un entero positivo."
        )

    return id_pelicula
