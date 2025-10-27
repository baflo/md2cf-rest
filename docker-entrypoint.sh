#!/bin/bash
set -e

# Docker entrypoint script for md2cf
# All commands are now handled through the md2cf CLI

# If no arguments provided, show help
if [ $# -eq 0 ]; then
    exec md2cf --help
fi

# If first argument doesn't start with a dash and is not "md2cf", prepend "md2cf"
if [[ "$1" != -* ]] && [ "$1" != "md2cf" ]; then
    # Arguments like "api", "publish", "convert", etc.
    exec md2cf "$@"
fi

# If first argument is "md2cf", execute as-is
if [ "$1" = "md2cf" ]; then
    exec "$@"
fi

# For arguments starting with dash (like --help), pass to md2cf
exec md2cf "$@"
