from decimal import Decimal, InvalidOperation


EXTENSIONES_PERMITIDAS = {"png", "jpg", "jpeg", "webp"}


def archivo_permitido(nombre_archivo):
    return (
        isinstance(nombre_archivo, str)
        and "." in nombre_archivo
        and nombre_archivo.rsplit(".", 1)[1].lower() in EXTENSIONES_PERMITIDAS
    )


def validar_servicio(datos):
    if not isinstance(datos, dict):
        raise ValueError("Se esperaba un objeto JSON")

    nombre = datos.get("nombre")
    descripcion = datos.get("descripcion")
    valor = datos.get("precio")

    if not isinstance(nombre, str) or not nombre.strip() or len(nombre.strip()) > 100:
        raise ValueError("Nombre inválido")

    if not isinstance(descripcion, str) or not descripcion.strip() or len(descripcion.strip()) > 250:
        raise ValueError("La descripción es inválida o supera los 250 caracteres")

    if not isinstance(valor, str):
        raise ValueError("Precio inválido")

    try:
        precio = Decimal(valor.strip())
    except (InvalidOperation, TypeError):
        raise ValueError("Precio inválido")

    if (
        not precio.is_finite()
        or precio <= 0
        or precio > Decimal("99999999.99")
        or precio.as_tuple().exponent < -2
    ):
        raise ValueError(
            "El precio debe ser positivo, tener como máximo dos decimales "
            "y no superar 99999999.99"
        )

    return nombre.strip(), descripcion.strip(), precio
