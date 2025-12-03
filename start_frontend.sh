#!/usr/bin/env bash
set -e

PORT="${1:-3000}"
echo "Serving frontend at http://127.0.0.1:${PORT}"
python3 -m http.server "$PORT"