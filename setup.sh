#!/bin/bash

# Terminar si ocurre un error
set -e

echo "===================================================="
echo "Iniciando Setup Completo NATIVO (BCC, Python, Flask y MySQL)"
echo "===================================================="

# --- PARTE 1: INSTALACIONES DE SISTEMA (Pide sudo internamente) ---
echo "Actualizando los índices de paquetes (requiere sudo)..."
sudo apt-get update -y

echo "Instalando Python3, herramientas de desarrollo y BCC..."
sudo apt-get install -y python3 python3-pip python3-venv python3-dev build-essential \
                        linux-headers-$(uname -r) bpfcc-tools python3-bpfcc libbpfcc

# --- PARTE 2: CONFIGURACIÓN DEL ENTORNO VIRTUAL ---
echo "Creando el entorno virtual usando el estándar .venv..."
python3 -m venv .venv

# Activar el entorno virtual para el resto del script
echo "Activando el entorno virtual..."
source .venv/bin/activate

# --- PARTE 3: INSTALACIÓN DE DEPENDENCIAS EN EL ENTORNO ---
echo "Instalando dependencias desde requirements.txt dentro del entorno virtual..."
pip install --upgrade pip

if [ -f requirements.txt ]; then
    pip install -r requirements.txt
    echo "¡Todas las librerías de requirements.txt se instalaron correctamente!"
else
    echo "Error: No se encontró el archivo requirements.txt en esta carpeta."
    exit 1
fi

# Instalar librerías adicionales pasadas por el usuario si existen
if [ $# -gt 0 ]; then
    echo "Instalando librerías adicionales: $@"
    pip install "$@"
fi

# --- PARTE 4: VERIFICACIÓN DE SEGURIDAD Y CONFIGURACIÓN (.env) ---
echo "----------------------------------------------------"
echo "Verificando configuración de seguridad..."

if [ ! -f .env ]; then
    echo "Atención: No se encontró el archivo .env en la raíz."
    echo "Creando un archivo .env de ejemplo con claves seguras..."
    
    # Generar claves aleatorias seguras automáticamente para facilitarlo
    SECRET_KEY_GEN=$(python3 -c "import os; print(os.urandom(32).hex())")
    JWT_SECRET_KEY_GEN=$(python3 -c "import os; print(os.urandom(32).hex())")
    
    cat << EOF > .env
SECRET_KEY=$SECRET_KEY_GEN
JWT_SECRET_KEY=$JWT_SECRET_KEY_GEN
# Agrega aquí tus credenciales de MySQL si las usas:
# DB_HOST=localhost
# DB_USER=tu_usuario
# DB_PASSWORD=tu_contraseña
# DB_NAME=cine_paradiso
EOF
    echo "¡Archivo .env generado automáticamente con llaves seguras!"
else
    echo "Archivo .env detectado correctamente."
fi

echo "----------------------------------------------------"
echo "¡Todo configurado con éxito!"
echo "===================================================="
echo "Para trabajar en este proyecto, recuerda activar tu entorno con:"
echo "source .venv/bin/activate"
echo ""
echo "Y luego puedes ejecutar tu servidor simplemente con:"
echo "python main.py"
echo "===================================================="
