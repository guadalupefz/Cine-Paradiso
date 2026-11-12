import os
import requests

OMDB_URL = "https://www.omdbapi.com/"
TIMEOUT = 10

class OMDbError(Exception):
    """Error producido durante una consulta a OMDb"""
    pass

def _obtener_api_key():
    api_key = os.getenv("OMDB_API_KEY")

    if not api_key:
        raise OMDbError("No está configurada la API Key de OMDb.")

    return api_key
