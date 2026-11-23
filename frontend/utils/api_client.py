import os
from pathlib import Path
from dotenv import load_dotenv
from flask import session
import requests

# Carga de variables de entorno (.env en la raíz del proyecto)
RAIZ = Path(__file__).resolve().parent.parent.parent
load_dotenv(RAIZ / ".env")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:5001/api").rstrip("/")
BACKEND_ORIGEN = BACKEND_URL.rsplit("/api", 1)[0]


def llamar_backend(metodo, ruta, **argumentos):
    
    #Realiza una petición HTTP a la API REST del backend.
    #Inyecta automáticamente la cabecera Authorization Bearer si el usuario inició sesión.
    
    cabeceras = {}
    if session.get("backend_token"):
        cabeceras["Authorization"] = "Bearer " + session["backend_token"]

    try:
        respuesta = requests.request(
            metodo,
            BACKEND_URL + ruta,
            headers=cabeceras,
            timeout=15,
            **argumentos
        )
        try:
            datos = respuesta.json()
        except ValueError:
            datos = {"error": "El backend devolvió una respuesta no válida."}
        return datos, respuesta.status_code

    except requests.RequestException:
        return {
            "error": "No se pudo conectar con el servidor. Intentá nuevamente."
        }, 503


def mensaje_error(datos):
    
    #Extrae y formatea un mensaje de error legible desde la respuesta JSON del backend.
    #Soporta múltiples estructuras (lista de 'errors', 'mensaje', 'message' o 'error').
    
    if isinstance(datos, dict):
        errores = datos.get("errors")
        if errores:
            return "; ".join(e.get("message", "Datos inválidos") for e in errores)
        return (
            datos.get("mensaje")
            or datos.get("message")
            or datos.get("error")
            or "No se pudo completar la operación."
        )
    return "No se pudo completar la operación."


def lista(datos, clave):
    
    #Garantiza la extracción segura de una lista desde la respuesta JSON,
    #previniendo fallos si la API devuelve directamente una lista o un diccionario con la clave.
    
    if isinstance(datos, list):
        return datos
    if isinstance(datos, dict):
        return datos.get(clave, [])
    return []