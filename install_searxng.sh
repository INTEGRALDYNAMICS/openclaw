#!/usr/bin/env bash
# install_searxng.sh — Instala y corre SearXNG sin Docker
# Uso: bash install_searxng.sh
# Luego: bash ~/.local/searxng/run_searxng.sh

set -e

SEARXNG_DIR="$HOME/.local/searxng"
PORT=8080

echo "=== Instalando SearXNG (sin Docker) ==="

# 1. Dependencias Python
echo "[1/4] Verificando dependencias..."
python3 -m pip install --user virtualenv 2>/dev/null || true

# 2. Crear virtualenv y clonar
mkdir -p "$SEARXNG_DIR"
if [ ! -d "$SEARXNG_DIR/venv" ]; then
  python3 -m venv "$SEARXNG_DIR/venv"
fi

# 3. Instalar SearXNG
echo "[2/4] Instalando SearXNG en virtualenv..."
source "$SEARXNG_DIR/venv/bin/activate"
pip install --quiet searxng 2>&1 | tail -3 || {
  echo "  → pip install searxng falló, clonando desde git..."
  git clone --depth=1 https://github.com/searxng/searxng.git "$SEARXNG_DIR/repo" 2>/dev/null || \
    (cd "$SEARXNG_DIR/repo" && git pull)
  pip install --quiet -e "$SEARXNG_DIR/repo"
}

# 4. Config con JSON habilitado
echo "[3/4] Creando configuración..."
mkdir -p "$SEARXNG_DIR/conf"
cat > "$SEARXNG_DIR/conf/settings.yml" << 'YAML'
use_default_settings: true
server:
  secret_key: "openclaw-searxng-local-secret"
  bind_address: "127.0.0.1"
  port: 8080
  public_instance: false
search:
  formats:
    - html
    - json
YAML

# 5. Script de arranque
echo "[4/4] Creando script de arranque..."
cat > "$SEARXNG_DIR/run_searxng.sh" << SCRIPT
#!/usr/bin/env bash
source "$SEARXNG_DIR/venv/bin/activate"
export SEARXNG_SETTINGS_PATH="$SEARXNG_DIR/conf/settings.yml"
cd "$SEARXNG_DIR"
echo "🔍 SearXNG corriendo en http://localhost:${PORT}"
echo "   Presiona Ctrl+C para detener"
python3 -m searx.webapp 2>&1 | grep -v DEBUG
SCRIPT
chmod +x "$SEARXNG_DIR/run_searxng.sh"

echo ""
echo "✅ Instalación completa!"
echo "   Inicia SearXNG con: bash ~/.local/searxng/run_searxng.sh"
echo "   O en background:    bash ~/.local/searxng/run_searxng.sh &"
echo ""
echo "   Verifica que funciona:"
echo "   curl -s 'http://localhost:8080/search?q=test&format=json' | python3 -c \"import json,sys; print(len(json.load(sys.stdin).get('results',[])), 'results')\""
