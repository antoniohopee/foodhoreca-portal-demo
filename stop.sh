#!/usr/bin/env bash
# Ferma FoodHoreca Portal. Con --reset azzera anche il database (riparte dai seed).
set -euo pipefail
cd "$(dirname "$0")"

if [ "${1:-}" = "--reset" ]; then
    echo "→ Spengo i container e azzero il database..."
    docker compose down -v
    echo "✓ Fermato. Al prossimo avvio il DB riparte dai dati seed."
else
    echo "→ Spengo i container (i dati restano)..."
    docker compose down
    echo "✓ Fermato. I dati sono conservati. Usa './stop.sh --reset' per azzerare il DB."
fi
