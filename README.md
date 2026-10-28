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
Seguí estos pasos para configurar el entorno de desarrollo en tu máquina local que posea el sistema operativo Linux:
```
### CLONAR EL REPOSITORIO
```bash
git clone https://github.com
cd tu-repositorio
```

### INSTALAR DEPENDENCIAS

```bash
Ejecutar: bash setup.sh. 
Nota  El script tiene un comando sudo apt-get update, por lo que solicitará la contraseña del usuario.       

```
### VARIABLES DE ENTORNO

```bash
Crea un archivo `.env` en la raíz del proyecto basándote en el archivo `.env.example`:

  .env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=contraseña_base_datos
DB_NAME=nombre_base_datos
DB_PORT=3306
```
---
### EJECUTAR SCRIPT DE BASE DE DATOS
```
 Ejecutar int_db.sql que se encuentra en la carpeta backend/db.

```
###  USO / EJECUCION

Para iniciar el servidor en modo de desarrollo, ejecutá:

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

