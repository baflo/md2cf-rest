#!/bin/bash
# Client-Generierungs-Script für md2cf REST API

set -e

API_URL="http://localhost:8000/openapi.json"
OUTPUT_DIR="./clients"

echo "=========================================="
echo "md2cf REST API Client Generator"
echo "=========================================="
echo ""

# Prüfe ob Server läuft
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ ERROR: API Server ist nicht erreichbar!"
    echo "Bitte starten Sie den Server mit:"
    echo "  python -m uvicorn md2cf.rest_api:app --host 0.0.0.0 --port 8000"
    exit 1
fi

echo "✅ API Server läuft"
echo ""

# Exportiere OpenAPI Schema
echo "📥 Exportiere OpenAPI Schema..."
curl -s $API_URL > openapi.json
echo "✅ Schema gespeichert: openapi.json"
echo ""

function openapi-generator-cli() { docker run --network=host openapitools/openapi-generator-cli $@ ; }

# Prüfe ob OpenAPI Generator installiert ist
if ! command -v openapi-generator-cli &> /dev/null; then
    echo "⚠️  OpenAPI Generator CLI ist nicht installiert."
    echo ""
    echo "Installation:"
    echo "  npm install @openapitools/openapi-generator-cli -g"
    echo ""
    echo "Oder via Docker:"
    echo "  docker pull openapitools/openapi-generator-cli"
    echo ""
    exit 1
fi

# Erstelle Output-Verzeichnis
mkdir -p $OUTPUT_DIR

# Funktion zum Generieren eines Clients
generate_client() {
    local LANG=$1
    local DESC=$2

    echo "🔨 Generiere $DESC Client..."

    openapi-generator-cli generate \
        -i openapi.json \
        -g $LANG \
        -o $OUTPUT_DIR/$LANG \
        --skip-validate-spec \
        > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "   ✅ $DESC Client erstellt: $OUTPUT_DIR/$LANG"
    else
        echo "   ❌ Fehler beim Generieren des $DESC Clients"
    fi
}

# Definiere zu generierende Clients
# Format: "generator-name" "Beschreibung"
declare -a CLIENTS=(
    "typescript-axios:TypeScript (Axios)"
    "javascript:JavaScript/Node.js"
    "java:Java"
    "python:Python"
    "go:Go"
    "csharp:C# / .NET"
    "php:PHP"
)

echo "Verfügbare Clients:"
echo ""
for i in "${!CLIENTS[@]}"; do
    IFS=':' read -r lang desc <<< "${CLIENTS[$i]}"
    echo "  $((i+1)). $desc"
done
echo "  0. Alle Clients"
echo ""

read -p "Welchen Client möchten Sie generieren? (0-${#CLIENTS[@]}): " choice

if [ "$choice" = "0" ]; then
    echo ""
    echo "Generiere alle Clients..."
    echo ""
    for client in "${CLIENTS[@]}"; do
        IFS=':' read -r lang desc <<< "$client"
        generate_client "$lang" "$desc"
    done
elif [ "$choice" -ge 1 ] && [ "$choice" -le "${#CLIENTS[@]}" ]; then
    IFS=':' read -r lang desc <<< "${CLIENTS[$((choice-1))]}"
    echo ""
    generate_client "$lang" "$desc"
else
    echo "❌ Ungültige Auswahl"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Client-Generierung abgeschlossen!"
echo "=========================================="
echo ""
echo "Clients befinden sich in: $OUTPUT_DIR/"
echo ""
echo "Beispiel-Verwendung siehe: CLIENT_GENERATION.md"
