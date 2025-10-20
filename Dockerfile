# Multi-stage Dockerfile for md2cf REST API

# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy custom CA certificates if they exist
COPY rootfs /

# Update CA certificates
RUN update-ca-certificates

# Configure Python to use system CA bundle
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Configure pip for Nexus repository
RUN pip config set global.index-url https://repository.lvm.de/nexus/repository/pypi-group/simple && \
    pip config set global.trusted-host repository.lvm.de

# Copy application files
COPY pyproject.toml README.md ./
COPY md2cf/ ./md2cf/

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[rest]" && \
    pip install --no-cache-dir gunicorn

# Stage 2: Runtime
FROM python:3.12-slim

LABEL maintainer="your.email@example.com"
LABEL description="md2cf REST API - Markdown to Confluence converter"
LABEL version="0.1.0"

# Install CA certificates package
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy custom CA certificates if they exist
COPY rootfs/usr/local/share/ca-certificates/ /usr/local/share/ca-certificates/

# Update CA certificates
RUN update-ca-certificates

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash md2cf && \
    mkdir -p /app && \
    chown -R md2cf:md2cf /app

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=md2cf:md2cf md2cf/ ./md2cf/
COPY --chown=md2cf:md2cf pyproject.toml README.md ./

# Switch to non-root user
USER md2cf

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command: Production server with Gunicorn
CMD ["gunicorn", "md2cf.rest_api:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]
