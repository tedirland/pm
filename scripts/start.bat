@echo off
setlocal

set CONTAINER_NAME=kanban-studio
set IMAGE_NAME=kanban-studio
if "%PORT%"=="" set PORT=8000

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..
set DB_DIR=%PROJECT_DIR%\data

if not exist "%DB_DIR%" mkdir "%DB_DIR%"

echo Building image...
docker build -t %IMAGE_NAME% "%PROJECT_DIR%"

echo Starting container on port %PORT%...
docker run -d --name %CONTAINER_NAME% -p %PORT%:8000 -v "%DB_DIR%:/app/data" --env-file "%PROJECT_DIR%\.env" %IMAGE_NAME% 2>nul || (
    echo Container already exists. Restarting...
    docker start %CONTAINER_NAME%
)

echo Kanban Studio running at http://localhost:%PORT%
