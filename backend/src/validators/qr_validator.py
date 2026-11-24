def validar_datos_qr(datos):
    if not isinstance(datos, dict):
        return False, "Los datos tienen un formato inválido."

    qr_token = datos.get("qr_token")
    if not isinstance(qr_token, str):
        return False, "El QR tiene que ser un texto."

    qr_token = qr_token.strip()
    if not qr_token:
        return False, "El QR está vacío."

    id_funcion = datos.get("id_funcion")

    if not isinstance(id_funcion, int) or id_funcion <= 0:
        return False, "El ID de la función es inválido."

    return True, None
