# Docker Deployment für md2cf REST API

Vollständige Anleitung zur Verwendung von Docker mit md2cf.

## 🚀 Quick Start

### Einfachster Start

```bash
# Image bauen
make docker-build

# Container starten
make docker-run

# API testen
curl http://localhost:8000/health
```

**Fertig!** Die API läuft auf http://localhost:8000

---

## 📦 Docker Images

### Production Image (`Dockerfile`)

**Features:**
- ✅ Multi-stage Build (optimiert)
- ✅ Python 3.12 Slim
- ✅ Gunicorn mit 4 Workers
- ✅ Non-root User
- ✅ Health Check
- ✅ Klein (~150 MB)

```bash
# Bauen
make docker-build
# oder
docker build -t md2cf-rest:latest .

# Starten
make docker-run
# oder
docker run -d -p 8000:8000 --name md2cf-api md2cf-rest:latest
```

### Development Image (`Dockerfile.dev`)

**Features:**
- ✅ Hot-Reload (uvicorn --reload)
- ✅ Debugging Support (Port 5678)
- ✅ Volume Mounts für Live-Code-Änderungen
- ✅ Alle Dev-Dependencies

```bash
# Bauen
make docker-build-dev

# Starten
make docker-dev
```

---

## 🐳 Docker Compose

### Production Setup

```bash
# Alle Services starten
docker-compose up -d

# Logs anschauen
make docker-logs

# Stoppen
docker-compose down
```

**Gestartete Services:**
- `api` - Production API Server (Port 8000)

### Development Setup

```bash
# Development Services starten
make docker-compose-dev

# Oder manuell
docker-compose --profile dev up -d
```

**Gestartete Services:**
- `api-dev` - Development Server mit Hot-Reload (Port 8000)
- `watcher` - OpenAPI Schema Auto-Export

### Mit Nginx Reverse Proxy

```bash
# Production mit Nginx
docker-compose --profile production up -d
```

**Services:**
- `api` - API Server (intern)
- `nginx` - Reverse Proxy (Port 80/443)

---

## 📋 Makefile Commands

### Build Commands

```bash
make docker-build          # Production Image bauen
make docker-build-dev      # Development Image bauen
make docker-rebuild        # Clean + Build
make docker-test           # Image bauen und testen
```

### Run Commands

```bash
make docker-run            # Production Container starten
make docker-dev            # Development Container starten
make docker-compose-up     # Alle Services (docker-compose)
make docker-compose-dev    # Dev Services (docker-compose)
```

### Management Commands

```bash
make docker-stop           # Container stoppen
make docker-logs           # Logs anzeigen (Production)
make docker-logs-dev       # Logs anzeigen (Development)
make docker-shell          # Shell im Container
make docker-clean          # Alles aufräumen
```

---

## 🔧 Konfiguration

### Umgebungsvariablen

```bash
# Mit docker run
docker run -d \
  -p 8000:8000 \
  -e LOG_LEVEL=debug \
  -e WORKERS=2 \
  md2cf-rest:latest

# Mit docker-compose
# In docker-compose.yml unter environment:
environment:
  - LOG_LEVEL=info
  - WORKERS=4
```

**Verfügbare Variablen:**
- `LOG_LEVEL` - Logging Level (debug, info, warning, error)
- `WORKERS` - Anzahl Gunicorn Workers (default: 4)
- `HOST` - Bind Host (default: 0.0.0.0)
- `PORT` - Bind Port (default: 8000)

### Ports

```bash
# Production
docker run -p 8080:8000 md2cf-rest:latest  # API auf Port 8080

# Development mit Debugger
docker run -p 8000:8000 -p 5678:5678 md2cf-rest:dev
```

**Standard Ports:**
- `8000` - API Server
- `5678` - Python Debugger (nur Dev)
- `80/443` - Nginx (optional)

### Volumes

```bash
# Development mit Live-Code-Updates
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/md2cf:/app/md2cf \
  md2cf-rest:dev

# Logs persistent speichern
docker run -d \
  -p 8000:8000 \
  -v ./logs:/app/logs \
  md2cf-rest:latest
```

---

## 🏥 Health Checks

### Automatischer Health Check

Der Container hat einen eingebauten Health Check:

```bash
# Status prüfen
docker ps

# Details anzeigen
docker inspect --format='{{.State.Health.Status}}' md2cf-api
```

**Health Check Konfiguration:**
- Interval: 30s
- Timeout: 10s
- Start Period: 5s
- Retries: 3

### Manueller Health Check

```bash
# Von Host
curl http://localhost:8000/health

# Im Container
docker exec md2cf-api curl http://localhost:8000/health
```

---

## 🔒 Sicherheit

### Non-Root User

Der Container läuft als User `md2cf` (UID 1000):

```bash
# User prüfen
docker exec md2cf-api whoami
# Output: md2cf
```

### Minimale Attack Surface

- Slim Base Image (kein unnecessary packages)
- Multi-stage Build (keine Build-Tools im final Image)
- Nur notwendige Dependencies

### Security Scanning

```bash
# Mit Trivy
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image md2cf-rest:latest

# Mit Docker Scout
docker scout cves md2cf-rest:latest
```

---

## 📊 Monitoring & Logging

### Logs anzeigen

```bash
# Alle Logs
make docker-logs

# Logs folgen
docker logs -f md2cf-api

# Letzte 100 Zeilen
docker logs --tail 100 md2cf-api

# Mit Zeitstempel
docker logs -t md2cf-api
```

### Logging-Format

Production (Gunicorn):
```
[2025-10-20 10:00:00 +0000] [1] [INFO] Starting gunicorn 21.2.0
[2025-10-20 10:00:00 +0000] [1] [INFO] Listening at: http://0.0.0.0:8000
```

Development (Uvicorn):
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### Metriken

```bash
# Container Stats
docker stats md2cf-api

# Ressourcen-Limits setzen
docker run -d \
  --memory="512m" \
  --cpus="1.0" \
  -p 8000:8000 \
  md2cf-rest:latest
```

---

## 🚢 Production Deployment

### Docker Swarm

```bash
# Stack deployen
docker stack deploy -c docker-compose.yml md2cf

# Services anzeigen
docker service ls

# Service skalieren
docker service scale md2cf_api=3

# Stack entfernen
docker stack rm md2cf
```

### Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: md2cf-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: md2cf-api
  template:
    metadata:
      labels:
        app: md2cf-api
    spec:
      containers:
      - name: api
        image: md2cf-rest:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "250m"
---
apiVersion: v1
kind: Service
metadata:
  name: md2cf-api
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: md2cf-api
```

```bash
# Deployen
kubectl apply -f deployment.yaml

# Status prüfen
kubectl get pods
kubectl get services

# Logs anzeigen
kubectl logs -f deployment/md2cf-api
```

### CI/CD Integration

**GitHub Actions:**

```yaml
# .github/workflows/docker-build.yml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

**GitLab CI:**

```yaml
# .gitlab-ci.yml
docker-build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA $CI_REGISTRY_IMAGE:latest
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - docker push $CI_REGISTRY_IMAGE:latest
  only:
    - main
```

---

## 🐛 Troubleshooting

### Container startet nicht

```bash
# Logs prüfen
docker logs md2cf-api

# Container im Interactive Mode starten
docker run -it --rm md2cf-rest:latest /bin/bash

# Health Check Status
docker inspect md2cf-api | jq '.[0].State.Health'
```

### Port bereits belegt

```bash
# Anderen Port verwenden
docker run -d -p 8080:8000 md2cf-rest:latest

# Oder in docker-compose.yml:
ports:
  - "8080:8000"
```

### Zu wenig Speicher

```bash
# Ressourcen-Limits erhöhen
docker run -d \
  --memory="1g" \
  --memory-swap="2g" \
  -p 8000:8000 \
  md2cf-rest:latest
```

### Image zu groß

```bash
# Image Size prüfen
docker images md2cf-rest

# Layers analysieren
docker history md2cf-rest:latest

# Mit dive analysieren
dive md2cf-rest:latest
```

### Development: Code-Änderungen werden nicht übernommen

```bash
# Volume-Mounts prüfen
docker inspect md2cf-api-dev | jq '.[0].Mounts'

# Container neu starten
docker-compose restart api-dev

# Oder neu bauen
make docker-build-dev
docker-compose up -d api-dev
```

---

## 📈 Performance Tuning

### Worker-Anzahl optimieren

```bash
# Formel: (2 × CPU_CORES) + 1
# Für 4 CPU Cores: (2 × 4) + 1 = 9 Workers

docker run -d \
  -p 8000:8000 \
  -e WORKERS=9 \
  md2cf-rest:latest
```

### Memory Limits

```bash
# Production Empfehlung
docker run -d \
  --memory="512m" \
  --memory-reservation="256m" \
  -p 8000:8000 \
  md2cf-rest:latest
```

### Gunicorn Tuning

Eigene `gunicorn.conf.py` erstellen:

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
keepalive = 5
timeout = 30
graceful_timeout = 30
```

Dann im Dockerfile verwenden:

```dockerfile
CMD ["gunicorn", "md2cf.rest_api:app", "-c", "gunicorn.conf.py"]
```

---

## 🔗 Nützliche Links

- **Docker Docs**: https://docs.docker.com/
- **Docker Compose**: https://docs.docker.com/compose/
- **Gunicorn**: https://docs.gunicorn.org/
- **Uvicorn**: https://www.uvicorn.org/

---

## 📝 Cheat Sheet

```bash
# === Build ===
make docker-build              # Production Image
make docker-build-dev          # Development Image
make docker-test               # Test Image

# === Run ===
make docker-run                # Production
make docker-dev                # Development
make docker-compose-up         # Alle Services

# === Manage ===
make docker-stop               # Stoppen
make docker-logs               # Logs
make docker-shell              # Shell
make docker-clean              # Aufräumen

# === Inspect ===
docker ps                      # Laufende Container
docker images                  # Vorhandene Images
docker stats md2cf-api        # Ressourcen-Nutzung
docker inspect md2cf-api      # Alle Details

# === Cleanup ===
docker system prune            # Unused resources
docker system prune -a         # Alles (inkl. images)
docker volume prune            # Unused volumes
```
