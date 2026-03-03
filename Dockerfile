FROM node:22-slim AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install backend dependencies
COPY backend/pyproject.toml backend/
RUN cd backend && uv sync --no-dev --no-install-project

# Copy backend source
COPY backend/app backend/app

# Copy frontend static build
COPY --from=frontend-build /frontend/out /app/static

EXPOSE 8000

CMD ["backend/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "backend"]
