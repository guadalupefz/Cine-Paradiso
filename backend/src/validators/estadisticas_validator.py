from datetime import datetime


def validar_filtros_estadisticas(args):
    desde = args.get("desde")
    hasta = args.get("hasta")
    id_local_texto = args.get("id_local")

    id_local = None

    if id_local_texto:
        try:
            id_local = int(id_local_texto)
        except ValueError:
            return None, None, None, "El ID del local debe ser un número entero."

        if id_local <= 0:
            return None, None, None, "El ID del local debe ser positivo."

    try:
        if desde:
            datetime.strptime(desde, "%Y-%m-%d")

        if hasta:
            datetime.strptime(hasta, "%Y-%m-%d")
    except ValueError:
        return None, None, id_local, "Las fechas deben tener formato AAAA-MM-DD."

    if desde and hasta and desde > hasta:
        return None, None, id_local, "La fecha desde no puede ser posterior a hasta."

    return desde, hasta, id_local, None
