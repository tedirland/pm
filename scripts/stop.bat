@echo off
setlocal

set CONTAINER_NAME=kanban-studio

echo Stopping container...
docker stop %CONTAINER_NAME% 2>nul
docker rm %CONTAINER_NAME% 2>nul
echo Stopped.
