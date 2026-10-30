import argparse

import requests


parser = argparse.ArgumentParser(description="Prueba los endpoints de autenticacion")
parser.add_argument("--base-url", default="http://127.0.0.1:5001/api")
parser.add_argument("--email", required=True, help="Email existente en la tabla usuario")
parser.add_argument("--password", required=True, help="Password correcta del usuario")
parser.add_argument("--timeout", type=float, default=5.0, help="Timeout por solicitud, en segundos")
args = parser.parse_args()

wrong_password = args.password + "_incorrecta"


def verify(name, response, expected_status):
    print(f"{name}: HTTP {response.status_code}")
    if response.status_code != expected_status:
        raise AssertionError(
            f"Se esperaba {expected_status}, se recibio {response.status_code}: "
            f"{response.text}"
        )


# Login correcto
with requests.Session() as client:
    response = client.post(
        f"{args.base_url}/auth/login",
        json={"email": args.email, "password": args.password},
        timeout=args.timeout,
    )
    verify("Login correcto", response, 200)

    response = client.get(f"{args.base_url}/usuarios/me", timeout=args.timeout)
    verify("Me con sesion", response, 200)

    response = client.post(f"{args.base_url}/auth/logout", timeout=args.timeout)
    verify("Logout", response, 200)

    response = client.get(f"{args.base_url}/usuarios/me", timeout=args.timeout)
    verify("Me despues de logout", response, 401)

# Login incorrecto con una sesion independiente
with requests.Session() as client:
    response = client.post(
        f"{args.base_url}/auth/login",
        json={"email": args.email, "password": wrong_password},
        timeout=args.timeout,
    )
    verify("Login con password incorrecta", response, 401)

# Consultar me sin sesion
with requests.Session() as client:
    response = client.get(f"{args.base_url}/usuarios/me", timeout=args.timeout)
    verify("Me sin sesion", response, 401)

print("Todas las pruebas completaron correctamente")
