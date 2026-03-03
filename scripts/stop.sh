#!/usr/bin/env bash
set -e

CONTAINER_NAME="kanban-studio"

echo "Stopping container..."
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true
echo "Stopped."
