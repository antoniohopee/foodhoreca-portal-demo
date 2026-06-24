#!/usr/bin/env bash
# Avvia FoodHoreca Portal: motore Docker -> container -> browser.
set -euo pipefail
cd "$(dirname "$0")"

URL="http://localhost:8000"

# .env dai valori di esempio se manca
[ -f .env ] || cp .env.example .env

# 1) Assicura che il motore Docker sia attivo
if ! docker info >/dev/null 2>&1; then
    echo "→ Avvio Docker Desktop..."
    open -a Docker
    printf "→ Attendo il motore Docker"
    for _ in $(seq 1 60); do
        if docker info >/dev/null 2>&1; then echo " pronto."; break; fi
        printf "."; sleep 2
    done
    docker info >/dev/null 2>&1 || { echo; echo "✗ Docker non si è avviato. Apri Docker Desktop a mano e riprova."; exit 1; }
fi

# 2) Avvia lo stack (build solo se serve)
echo "→ Avvio container..."
docker compose up -d

# 3) Attendi che l'app risponda, poi apri il browser
printf "→ Attendo l'app su %s" "$URL"
for _ in $(seq 1 30); do
    if [ "$(curl -s -o /dev/null -w '%{http_code}' "$URL" 2>/dev/null)" = "200" ]; then
        echo " pronta."
        open "$URL"
        echo "✓ FoodHoreca Portal attivo: $URL"
        exit 0
    fi
    printf "."; sleep 2
done

echo
echo "⚠ L'app non ha ancora risposto. Controlla i log con:"
echo "    docker compose logs -f web"
exit 1
