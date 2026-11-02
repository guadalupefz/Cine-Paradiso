import re
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def validar_datos_registro(data):
    errores = []
    if not isinstance(data, dict):
        return [{"code": "DATOS_INVALIDOS", "message": "Se esperaba un objeto JSON.", "level": "error"}]
    for campo, limite in [("nombre", 100), ("apellido", 100), ("email", 150)]:
        valor = data.get(campo)
        if not isinstance(valor, str) or not valor.strip() or len(valor.strip()) > limite:
            errores.append({"code": "DATOS_INVALIDOS", "message": f"Revisá el campo {campo}.", "level": "error"})
    password = data.get("password")
    if not isinstance(password, str) or not password or len(password) > 256:
        errores.append({"code": "DATOS_INVALIDOS", "message": "La contraseña debe tener entre 1 y 256 caracteres.", "level": "error"})
    if errores:
        return errores
    if not re.fullmatch(EMAIL_REGEX, data["email"].strip()):
        errores.append({"code": "EMAIL_FORMATO_INVALIDO", "message": "El email no tiene un formato válido.", "level": "error"})
    return errores
