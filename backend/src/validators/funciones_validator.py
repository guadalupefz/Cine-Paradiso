from datetime import datetime
from decimal import Decimal, InvalidOperation


def validar_crear_funcion(data):
    if not isinstance(data, dict) or not data:
        return "No se proporcionaron datos en formato JSON."

    for campo in ("id_pelicula", "id_sala"):
        valor = data.get(campo)
        if type(valor) is not int or valor <= 0:
            return f"El campo {campo} debe ser un entero positivo."

    fecha = data.get("fecha_hora_inicio")
    if not isinstance(fecha, str) or not fecha.strip():
        return "El campo fecha_hora_inicio es obligatorio."

    try:
        datetime.fromisoformat(fecha)
    except ValueError:
        return "Formato de fecha_hora_inicio inválido. Utilice formato ISO (YYYY-MM-DDTHH:MM:SS)."

    precio = data.get("precio_base")
    if precio is None or isinstance(precio, bool):
        return "El campo precio_base debe ser un valor numérico."

    try:
        precio_decimal = Decimal(str(precio))
    except (InvalidOperation, ValueError):
        return "El precio_base debe ser un valor numérico."

    if not precio_decimal.is_finite():
        return "El precio_base debe ser un valor numérico finito."
    if precio_decimal < 0:
        return "El precio_base no puede ser negativo."
    if precio_decimal.as_tuple().exponent < -2:
        return "El precio_base admite como máximo dos decimales."

    return None
