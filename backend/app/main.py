import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.database import get_connection, init_db
from app.routers import ai, auth, boards, cards, columns

_default_static = Path(__file__).resolve().parent.parent.parent / "static"
STATIC_DIR = Path(os.environ.get("STATIC_DIR", str(_default_static)))


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_connection()
    init_db(conn)
    conn.close()
    yield


app = FastAPI(title="Kanban Studio API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(boards.router)
app.include_router(cards.router)
app.include_router(columns.router)
app.include_router(ai.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if STATIC_DIR.is_dir():
    @app.get("/")
    async def index():
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/_next", StaticFiles(directory=STATIC_DIR / "_next"), name="next-assets")
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:
    @app.get("/", response_class=HTMLResponse)
    async def index():
        return """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Kanban Studio</title></head>
<body>
<h1>Hello World</h1>
<p>Kanban Studio backend is running. No frontend build found.</p>
</body>
</html>"""
