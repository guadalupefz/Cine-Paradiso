
def validar_datos_qr(datos):
    if not isinstance(datos, dict):
        return False, "los daros tienen un formato invalido"

    qr_token = datos.get("qr_token")
    if not isinstance(qr_token, str):
        return False, "el qr tiene que ser un texto"

    qr_token = qr_token.strip()
    if not qr_token:
        return False, "el qr esta vacio"

    id_funcion = datos.get("id_funcion")

    if not isinstance(id_funcion, int) or id_funcion<= 0:
        return False, "el id de la funcion es invalido"

    return True, None