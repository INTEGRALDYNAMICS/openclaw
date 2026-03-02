#!/bin/bash
# openclaw-backup.sh — Backup de config y memorias a Git
# Ejecutar con cron: 0 */6 * * * /ruta/openclaw-backup.sh

BACKUP_DIR="/home/qu4ntum/.openclaw-backup"
OPENCLAW_DIR="/home/qu4ntum/.openclaw"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Inicializar repo si no existe
if [ ! -d "$BACKUP_DIR/.git" ]; then
    git -C "$BACKUP_DIR" init
    git -C "$BACKUP_DIR" config user.email "qu4ntum@arcadia"
    git -C "$BACKUP_DIR" config user.name "qu4ntum"
fi

# Copiar archivos importantes (sin datos sensibles como API keys en logs)
cp "$OPENCLAW_DIR/openclaw.json" "$BACKUP_DIR/openclaw.json" 2>/dev/null
cp "$OPENCLAW_DIR/cron/jobs.json" "$BACKUP_DIR/cron-jobs.json" 2>/dev/null
cp "$OPENCLAW_DIR/workspace/MEMORY.md" "$BACKUP_DIR/MEMORY.md" 2>/dev/null

# Backup del historial SQLite de Mem0 (las memorias reales)
if [ -f "$OPENCLAW_DIR/memory/mem0-history.sqlite" ]; then
    cp "$OPENCLAW_DIR/memory/mem0-history.sqlite" "$BACKUP_DIR/mem0-history.sqlite"
fi

# Commit
cd "$BACKUP_DIR"
git add -A
git diff --staged --quiet || git commit -m "backup: $DATE"

# Si hay remote configurado, push
if git remote | grep -q "origin"; then
    git push origin main --quiet && echo "$(date): Backup pusheado a GitHub" || echo "$(date): Push falló (sin internet?)"
else
    echo "$(date): Backup local guardado en $BACKUP_DIR"
    echo "Para pushear a GitHub: git -C $BACKUP_DIR remote add origin https://github.com/TU_USER/openclaw-backup"
fi
