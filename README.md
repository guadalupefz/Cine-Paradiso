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
## INSTALACION Y CONFIGURACION
```
Siga estos pasos para configurar el entorno de desarrollo en su máquina local que posea el sistema operativo Linux:
```
### CLONAR EL REPOSITORIO
```bash
git clone https://github.com
cd su-repositorio
```

### CONFIGURACION DE CREDENCIALES Y ENTORNO

```
Para poner en marcha el proyecto, necesita configurar las variables de entorno adquiriendo una clave para la API externa de películas y generando una clave secreta para la seguridad de los tokens (JWT).
```

#### OBTENCION DE LA API KEY DE OMDb
```

Esta clave es necesaria para consumir el listado de películas.
1. Ingrese al sitio web oficial de OMDb API.(http://omdbapi.com'). Registrese.
2. Haga clic en la opción API Key en el menú superior derecho.
3. Seleccione el tipo de cuenta FREE (gratuita, permite hasta 1,000 solicitudes diarias).
4. Complete el formulario con su correo electrónico y los datos solicitados.
5. Recibirá un correo de confirmación con tu clave de API. Cópiela así "OMDB_API_KEY"="SU_CLAVE_API"
```
#### GENERACION DEL SECRET KEY PARA JWT
```
Para habilitar los mecanismos de seguridad y autenticación de la API, necesitas generar una clave secreta robusta:
 1 ingrese el comando "openssl rand -base64 32" en la terminal de linux. Le va a generar una clave.-
 2 Guarde esa clave en "JWT_SECRET_KEY" en un archivo .env en su proyecto.-
```

### VARIABLES DE ENTORNO
```
 Cree un archivo `.env` en la raíz del proyecto basándose en el siguiente archivo `.env.example`:
```

```bash

  .env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=contraseña_base_datos
DB_NAME=cine_paradiso
DB_PORT=3306
JWT_SECRET_KEY = SU_TOKEN_JWT
OMDB_API_KEY =  SU_API_KEY
```
---
### INSTALAR DEPENDENCIAS

```bash
Ejecutar: bash setup.sh. 
Nota  El script tiene un comando sudo apt-get update, por lo que solicitará la contraseña del usuario.       

```

### EJECUTAR SCRIPT DE BASE DE DATOS
```
 Ejecute int_db.sql que se encuentra en la carpeta backend/db.

```
###  USO / EJECUCION

Para iniciar el servidor en modo de desarrollo, ejecute:

```
 source .venv/bin/activate para activar el entorno virtual.
 python3 app.py

```

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

