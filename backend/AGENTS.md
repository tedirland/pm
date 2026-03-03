# Backend

## Overview

Python FastAPI backend serving the Kanban Studio API and static frontend assets. Packaged with uv, runs via uvicorn inside Docker.

## Structure

- `app/main.py` -- FastAPI application. Currently serves a hello-world HTML page at / and a health check at /api/health.
- `app/__init__.py` -- Package init.
- `tests/test_main.py` -- Async pytest tests for all endpoints using httpx ASGITransport.
- `pyproject.toml` -- Project config. Dependencies: fastapi, uvicorn. Dev: pytest, httpx, pytest-asyncio. Asyncio mode set to auto.

## Running tests

```
cd backend
uv sync --all-extras
uv run pytest tests/ -v
```

## Key conventions

- All endpoints are async.
- Tests use httpx AsyncClient with ASGITransport (no real server needed).
- pytest-asyncio in auto mode (no @pytest.mark.asyncio decorators needed).