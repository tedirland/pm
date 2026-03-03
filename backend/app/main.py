import os
from pathlib import Path

from fastapi import Cookie, FastAPI, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Kanban Studio API")

STATIC_DIR = Path(os.environ.get("STATIC_DIR", str(Path(__file__).resolve().parent.parent.parent / "static")))

VALID_USERNAME = "user"
VALID_PASSWORD = "password"
SESSION_TOKEN = "valid-session"


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/login")
async def login(body: LoginRequest, response: Response):
    if body.username == VALID_USERNAME and body.password == VALID_PASSWORD:
        response.set_cookie(key="session", value=SESSION_TOKEN, httponly=True, samesite="lax")
        return {"username": body.username}
    return Response(status_code=401, content='{"error":"Invalid credentials"}', media_type="application/json")


@app.post("/api/logout")
async def logout(response: Response):
    response.delete_cookie(key="session")
    return {"ok": True}


@app.get("/api/me")
async def me(session: str | None = Cookie(default=None)):
    if session == SESSION_TOKEN:
        return {"username": VALID_USERNAME}
    return Response(status_code=401, content='{"error":"Not authenticated"}', media_type="application/json")


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
