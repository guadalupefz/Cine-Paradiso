"""Crear una cuenta administrativa desde la terminal, nunca desde registro publico."""
import argparse
from getpass import getpass
import mysql.connector
from werkzeug.security import generate_password_hash
from backend.db.db import get_connection

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email")
    parser.add_argument("--nombre",default="Administrador")
    argumentos = parser.parse_args()
    password = getpass("Contraseña de la nueva cuenta: ")
    if len(password) < 12 or password != getpass("Repetir contraseña: "):
        parser.error("Usá al menos 12 caracteres y repetí la misma contraseña.")
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("INSERT INTO usuario (nombre,apellido,email,password_hash,rol) VALUES (%s,%s,%s,%s,%s)", (argumentos.nombre,"Administración",argumentos.email.strip().lower(),generate_password_hash(password),"administrador"))
        conexion.commit()
        print("Cuenta administrativa creada.")
    except mysql.connector.Error:
        conexion.rollback()
        raise
    finally:
        conexion.close()

if __name__ == "__main__":
    main()
