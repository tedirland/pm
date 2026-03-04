# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kanban Studio - a Project Management MVP with AI-powered card management. Users sign in, view a Kanban board, drag-drop cards between columns, and chat with an AI that can create/edit/move cards.

## Tech Stack

- **Frontend:** Next.js 16 with React 19, Tailwind CSS 4, @dnd-kit for drag-drop
- **Backend:** Python FastAPI with SQLite (raw SQL, no ORM)
- **AI:** OpenRouter API using `openai/gpt-oss-120b` model
- **Deployment:** Docker container with frontend static export served by FastAPI

## Commands

### Frontend (from `frontend/`)
```bash
npm run dev           # Dev server at :3000
npm run build         # Static export to ./out
npm run lint          # ESLint
npm run test:unit     # Vitest unit tests
npm run test:e2e      # Playwright e2e tests
npm run test:all      # All tests
```

### Backend (from `backend/`)
```bash
uv sync               # Install dependencies
pytest                # Run tests
pytest tests/test_main.py::test_name  # Single test
```

### Docker
```bash
./scripts/start.sh    # Build and run on port 8000
./scripts/stop.sh     # Stop container
```

## Architecture

```
frontend/
  src/app/           # Next.js routes (page.tsx entry point)
  src/components/    # React components (KanbanBoard, ChatSidebar, CardModal, etc.)
  src/lib/           # API client (api.ts), Kanban logic (kanban.ts)

backend/
  app/main.py        # FastAPI routes, auth, request/response models
  app/database.py    # SQLite schema and CRUD operations
  app/ai.py          # OpenRouter AI integration, response parsing
```

## Key Implementation Details

**ID Prefixing:** Column IDs use "col-" prefix, card IDs use "card-" prefix. The `parse_id()` function in main.py strips prefixes for DB queries. This prevents dnd-kit from confusing columns and cards.

**Auth (MVP only):** Hardcoded `SESSION_TOKEN = "valid-session"` cookie. `get_authenticated_user_id()` validates session and auto-creates user/board via `ensure_user()`/`ensure_board()`. Credentials: "user"/"password". **This must be replaced with proper authentication (OAuth, JWT, etc.) before production.**

**Database:** SQLite at `/app/data/kanban.db`. One board per user. 5 default columns + 8 sample cards seeded on board initialization.

**Frontend API Client:** `frontend/src/lib/api.ts` - all API calls use relative paths (no base URL needed since FastAPI serves everything).

**Optimistic Updates:** `KanbanBoard.tsx` updates local state immediately, then calls the API. On error it calls `loadBoard()` to re-sync from server.

**AI Chat:** Board state sent as JSON context. AI returns `{"message": string, "board_updates": {...}}`. `_apply_board_updates()` in main.py resolves column titles to IDs so AI can reference columns by name. `parse_ai_response()` handles edge cases: unwraps nested responses (model sometimes wraps in `{"final":{...}}`), returns fallback message on empty `{}`.

**AI Conversation History:** Kept in React state (ChatSidebar), lost on refresh. `FormattedMessage` sub-component renders lightweight markdown (bold, italic, bullet lists).

**Static Export:** Frontend builds to `out/`, served by FastAPI StaticFiles mount at root path.

**Docker Rebuild:** Use `--no-cache` if frontend changes aren't appearing. Browser hard refresh (Cmd+Shift+R) may also be needed.

## Environment

- `OPENROUTER_API_KEY` in `.env` (required for AI features)
- `DB_PATH` defaults to `/app/data/kanban.db`

## Color Scheme

- Accent Yellow: `#ecad0a`
- Blue Primary: `#209dd7`
- Purple Secondary: `#753991`
- Dark Navy: `#032147`
- Gray Text: `#888888`

## Test Counts

- Backend: 41 pytest tests
- Frontend unit: 19 vitest tests
- E2E: 5 playwright tests

## Coding Standards

1. Use latest library versions and idiomatic approaches
2. Keep it simple - never over-engineer
3. Be concise - minimal documentation, no emojis
4. Always identify root cause before fixing (prove with evidence)
