from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Kanban Studio API")


@app.get("/", response_class=HTMLResponse)
async def index():
    return """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Kanban Studio</title></head>
<body>
<h1>Hello World</h1>
<p>Kanban Studio backend is running.</p>
</body>
</html>"""


@app.get("/api/health")
async def health():
    return {"status": "ok"}
