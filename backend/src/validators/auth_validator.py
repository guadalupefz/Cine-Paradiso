import re


def validar_datos_registro(data):

    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    errores = []

    if not isinstance(data, dict):
        return [{
            "code": "DATOS_INVALIDOS",
            "message": "Se esperaba un objeto JSON.",
            "level": "error"
        }]

    for campo, limite in [("nombre", 100), ("apellido", 100), ("email", 150)]:
        valor = data.get(campo)

        if not isinstance(valor, str) or not valor.strip() or len(valor.strip()) > limite:
            errores.append({
                "code": "DATOS_INVALIDOS",
                "message": f"Revisá el campo {campo}.",
                "level": "error"
            })

    password = data.get("password")

    if not isinstance(password, str) or not password or len(password) > 256:
        errores.append({
            "code": "DATOS_INVALIDOS",
            "message": "La contraseña debe tener entre 1 y 256 caracteres.",
            "level": "error"
        })

    if errores:
        return errores

    if not re.fullmatch(email_regex, data["email"].strip()):
        errores.append({
            "code": "EMAIL_FORMATO_INVALIDO",
            "message": "El email no tiene un formato válido.",
            "level": "error"
        })

    return errores

def validar_datos_login(datos):
    errores = []

    if not isinstance(datos, dict):
        return [{
            "code": "JSON_INVALIDO",
            "message": "El cuerpo de la petición debe ser un JSON válido.",
            "level": "error"
        }]

    email = datos.get("email")
    password = datos.get("password")

    if not isinstance(email, str) or not email.strip():
        errores.append({
            "code": "DATOS_INVALIDOS",
            "message": "El campo email es obligatorio y debe ser un texto.",
            "level": "error"
        })

    if not isinstance(password, str) or not password or len(password) > 256:
        errores.append({
            "code": "DATOS_INVALIDOS",
            "message": "La contraseña debe tener entre 1 y 256 caracteres.",
            "level": "error"
        })

    return errores