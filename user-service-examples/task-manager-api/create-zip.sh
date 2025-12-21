#!/bin/bash
# Script para crear el archivo ZIP del servicio Task Manager API

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📦 Creando archivo ZIP del Task Manager API..."

# Crear el archivo ZIP excluyendo archivos innecesarios
zip -r task-manager-api.zip . \
  -x "*.git*" \
  -x "*.zip" \
  -x "*.tar.gz" \
  -x "*.db" \
  -x "*.sqlite*" \
  -x "create-zip.sh" \
  -x "README.md" \
  -x ".env*" \
  -x "__pycache__/*" \
  -x "*.pyc" \
  -x "*.pyo" \
  -x "data/*"

echo "✅ Archivo creado: task-manager-api.zip"
echo ""
echo "📋 Contenido del ZIP:"
unzip -l task-manager-api.zip | grep -E "\.(py|txt|Dockerfile)" || true
echo ""
echo "🚀 Ahora puedes subir 'task-manager-api.zip' desde la UI en http://localhost:3000"
