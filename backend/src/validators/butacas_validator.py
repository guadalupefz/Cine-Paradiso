def validar_butacas(data):
    if not isinstance(data, dict) or not isinstance(data.get("butacas"), list):
        return None, "Se requiere una lista de butacas."

    butacas = data["butacas"]

    if not butacas:
        return None, "La sala debe tener al menos una butaca."

    claves = []

    for butaca in butacas:
        if not isinstance(butaca, dict):
            return None, "Cada butaca debe tener fila y número."

        fila = butaca.get("fila")
        numero = butaca.get("numero")

        if (
            not isinstance(fila, str)
            or not fila.strip()
            or len(fila.strip()) > 5
            or not fila.strip().isalpha()
        ):
            return None, "La fila debe contener entre 1 y 5 letras."

        if type(numero) is not int or numero <= 0:
            return None, "El número de butaca debe ser positivo."

        claves.append((fila.strip().upper(), numero))

    if len(claves) != len(set(claves)):
        return None, "No puede haber butacas repetidas."

    return claves, None
