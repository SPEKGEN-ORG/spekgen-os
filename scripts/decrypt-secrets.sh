#!/bin/bash
# decrypt-secrets.sh — Descifra secrets/credentials.env.enc en ~/.env.spekgen.
# Uso (Mac/Linux): bash scripts/decrypt-secrets.sh
# El script te pide el password de forma interactiva (no se imprime).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENC_FILE="$REPO_ROOT/secrets/credentials.env.enc"
OUT_FILE="$HOME/.env.spekgen"

if [ ! -f "$ENC_FILE" ]; then
    echo "ERROR: No existe $ENC_FILE. ¿Repo cloneado completo?" >&2
    exit 1
fi

if ! command -v openssl >/dev/null; then
    echo "ERROR: openssl no instalado. Mac viene con uno; Linux: apt install openssl." >&2
    exit 1
fi

echo "Descifrando credenciales SPEKGEN."
echo "Password te lo da Gibran por Signal/WhatsApp."
echo

# Backup previo si existe
if [ -f "$OUT_FILE" ]; then
    cp "$OUT_FILE" "$OUT_FILE.bak.$(date +%Y%m%d-%H%M%S)"
    echo "Backup previo: $OUT_FILE.bak.*"
fi

# Decrypt — pedirá password interactivamente
openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -d \
    -in "$ENC_FILE" \
    -out "$OUT_FILE"

chmod 600 "$OUT_FILE"

echo
echo "✓ Descifrado en $OUT_FILE (modo 600 — solo tú lees)"
echo "  $(grep -c '^[A-Z_]' "$OUT_FILE") variables disponibles"
echo
echo "Scripts del repo cargan este archivo con python-dotenv automáticamente."
