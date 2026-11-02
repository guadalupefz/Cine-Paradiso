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
La autenticación integrada utiliza sesiones de Flask; no requiere generar tokens JWT.

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

