#!/bin/bash
# Script para crear el archivo ZIP del servicio de ejemplo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📦 Creando archivo ZIP del servicio de ejemplo..."

# Crear el archivo ZIP excluyendo archivos innecesarios
zip -r example-service.zip . \
  -x "*.git*" \
  -x "*.zip" \
  -x "*.tar.gz" \
  -x "create-zip.sh" \
  -x "README.md"

echo "✅ Archivo creado: example-service.zip"
echo ""
echo "📋 Contenido del ZIP:"
unzip -l example-service.zip | grep -E "\.(py|txt|Dockerfile)" || true
echo ""
echo "🚀 Ahora puedes subir 'example-service.zip' desde la UI en http://localhost:3000"
