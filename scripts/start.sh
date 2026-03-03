#!/usr/bin/env bash
set -e

CONTAINER_NAME="kanban-studio"
IMAGE_NAME="kanban-studio"
PORT="${PORT:-8000}"
DB_DIR="$(cd "$(dirname "$0")/.." && pwd)/data"

mkdir -p "$DB_DIR"

echo "Building image..."
docker build -t "$IMAGE_NAME" "$(dirname "$0")/.."

echo "Starting container on port $PORT..."
docker run -d \
  --name "$CONTAINER_NAME" \
  -p "$PORT:8000" \
  -v "$DB_DIR:/app/data" \
  --env-file "$(dirname "$0")/../.env" \
  "$IMAGE_NAME" 2>/dev/null || {
    echo "Container already exists. Restarting..."
    docker start "$CONTAINER_NAME"
  }

echo "Kanban Studio running at http://localhost:$PORT"
