#!/bin/bash
set -e

# Docker entrypoint script for md2cf
# Supports both REST API mode and CLI mode

# If no arguments or first argument is a known server command, start REST API
if [ $# -eq 0 ] || [ "$1" = "gunicorn" ] || [ "$1" = "uvicorn" ]; then
    echo "Starting md2cf REST API server..."
    exec gunicorn md2cf.rest_api:app \
        --workers "${WORKERS:-4}" \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind "0.0.0.0:${PORT:-8000}" \
        --access-logfile - \
        --error-logfile - \
        --log-level "${LOG_LEVEL:-info}"
fi

# If first argument is "md2cf", run CLI command
if [ "$1" = "md2cf" ]; then
    echo "Running md2cf CLI command: $*"
    exec "$@"
fi

# Otherwise, execute the command as-is
echo "Executing command: $*"
exec "$@"
