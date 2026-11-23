from pathlib import Path
from urllib.parse import urljoin
from flask import url_for

from frontend.utils.api_client import BACKEND_ORIGEN


def resolver_url_poster(poster):
    
    #Normaliza y resuelve la URL completa para visualizar la imagen del póster.
    
    #Maneja tres casos:
    #1. URL absoluta (http:// o https://): Se retorna intacta.
    #2. Ruta relativa estática (static/...): Se verifica si es un recurso local
    #   del frontend o si se encuentra servido por el servidor backend.
    #3. Valor nulo o vacío: Retorna la imagen por defecto (poster_sin_imagen.svg).
    
    if not poster or not isinstance(poster, str):
        return url_for("static", filename="img/poster_sin_imagen.svg")

    valor = poster.strip()
    if valor.startswith(("http://", "https://")):
        return valor

    ruta_poster = valor.lstrip("/")
    if ruta_poster.startswith("static/"):
        # Verificar si el archivo existe físicamente en la carpeta static del frontend
        archivo_local = (
            Path(__file__).resolve().parent.parent
            / "static"
            / ruta_poster.removeprefix("static/")
        )
        if archivo_local.is_file():
            return url_for("static", filename=ruta_poster.removeprefix("static/"))

        # Si no es un archivo local del frontend, se une con la URL del backend
        return urljoin(BACKEND_ORIGEN + "/", ruta_poster)

    return url_for("static", filename="img/poster_sin_imagen.svg")


def obtener_servicios_seleccionados(texto):
    
    #Parsea la cadena de texto de servicios seleccionados recibida por URL
    #(ejemplo: "1:2,3:1") y la convierte en una lista de diccionarios.
    
    #Lanza ValueError si el formato es inválido o contiene IDs/cantidades erróneas.
    
    if not texto:
        return []

    servicios = []
    ids = set()

    for elemento in texto.split(","):
        partes = elemento.split(":")

        if len(partes) != 2:
            raise ValueError("Formato de servicios inválido")

        try:
            id_servicio = int(partes[0])
            cantidad = int(partes[1])
        except ValueError:
            raise ValueError("Formato numérico de servicios inválido")

        if id_servicio <= 0 or cantidad <= 0 or id_servicio in ids:
            raise ValueError("Selección de servicios inválida")

        servicios.append({
            "id_servicio": id_servicio,
            "cantidad": cantidad
        })
        ids.add(id_servicio)

    return servicios