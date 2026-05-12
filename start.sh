#!/bin/bash
# Script de arranque rápido para Combat Analyzer Pro
set -e

echo "=========================================="
echo "  Combat Analyzer Pro - Arranque rápido"
echo "=========================================="

# 1. Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    exit 1
fi

# 2. Crear venv si no existe
if [ ! -d "venv" ]; then
    echo "→ Creando entorno virtual..."
    python3 -m venv venv
fi

# 3. Activar venv
source venv/bin/activate

# 4. Instalar deps
echo "→ Instalando dependencias..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# 5. Verificar .env
if [ ! -f ".env" ]; then
    echo "⚠️  No existe .env. Copiando .env.example → .env"
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANTE: Edita .env y agrega tus API keys antes de continuar:"
    echo "   - GEMINI_API_KEY     (https://aistudio.google.com/apikey)"
    echo "   - ANTHROPIC_API_KEY  (https://console.anthropic.com)"
    echo "   - OPENAI_API_KEY     (https://platform.openai.com/api-keys)"
    echo ""
    read -p "Presiona ENTER cuando termines de editar .env..."
fi

# 6. Inicializar DB
echo "→ Inicializando base de datos..."
python -m app.core.init_db

# 7. Crear directorios
mkdir -p uploads reports

# 8. Arrancar
echo ""
echo "=========================================="
echo "  ✓ Listo. Servidor en http://localhost:8000"
echo "=========================================="
echo ""

uvicorn app.main:app --reload --port 8000
