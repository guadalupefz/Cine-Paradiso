# CINE-PARADISO
---
```
Proyecto Integrador — Introducción al Desarrollo de Software
Cátedra: Lanzillotta
Período: Segundo cuatrimestre de 2026
```
## DESCRIPCIÓN DEL PROYECTO
```
Cine Paradiso es un sistema web para la gestión de un cine. El proyecto busca ofrecer una plataforma donde los usuarios puedan consultar la cartelera, conocer las funciones disponibles y gestionar la compra de entradas.
Además, contará con un backoffice para administrar la información del cine.
```
## OBJETIVOS
```
- Desarrollar una aplicación web utilizando Flask.
- Implementar una API backend para gestionar la lógica del sistema.
- Utilizar MySQL como sistema de gestión de base de datos.
- Conectar el frontend con el backend mediante solicitudes HTTP realizadas desde Python.
- Implementar mecanismos de autenticación y autorización.
- Generar y validar códigos QR asociados a las entradas.
```
## INSTALACIÓN Y EJECUCIÓN

La guía vigente está en [docs/integracion-hito2.md](docs/integracion-hito2.md).

```bash
git clone https://github.com/guadalupefz/Cine-Paradiso.git
cd Cine-Paradiso
git switch develop
bash init.sh
```

Completar `.env` desde `.env.example`, crear/cargar MySQL y activar `.venv`.
El backend se inicia con `python -m backend.app` y el frontend con `python frontend/app.py`.
La autenticación de la API utiliza Flask-JWT-Extended. El frontend envía el token desde Python. La configuración y la migración para bases existentes están en [Autenticación](docs/autenticacion.md).

## Ejecución con Docker Compose

Crear el archivo de entorno y definir al menos una contraseña real para MySQL:

```bash
cp .env.example .env
docker compose up --build
```

Los servicios quedan disponibles en:

- Frontend: http://127.0.0.1:8080
- Backend: http://127.0.0.1:5001/api
- MySQL: `127.0.0.1:3307`

Docker crea el usuario `cine_app`, definido por `DB_USER`, con acceso a la base
`cine_paradiso`. El esquema inicial se carga automáticamente la primera vez que
se crea el volumen `mysql_data`.

Para cargar datos ficticios después del primer arranque:

```bash
docker compose exec -T db sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' < backend/db/datos_prueba.sql
```

Si cambias usuario, contraseña o nombre de base después de haber creado el
volumen, recrea la base local con:

```bash
docker compose down -v
docker compose up --build
```

## CONEXIÓN Y AYUDANTES SQL

`backend/db/db.py` contiene `get_connection`. `backend/db/__init__.py` exporta
`ejecutar_buscar`, `ejecutar_buscar_uno` y `ejecutar_guardar`.
Importarlos desde `backend.db`; no hace falta otro archivo `backend/db.py`.

## GRUPO TP final IDS
```
GRUPO TP final IDS
- Integrante 1: Guadalupe Fernandez
- Integrante 2: Tiziana Gonzalez
- Integrante 3: Julieta Nágera
- Integrante 4: Sarai Slavkis
- Integrante 5: Carlos Sixto
- Integrante 6: Santino Muller
- Integrante 7: Alberto Parot
- Integrante 8: Matías Goro
- Integrante 9: Nicolas Merlo
- Integrante 10: Henry Luis

```

