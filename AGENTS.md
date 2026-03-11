# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kanban Studio - a Project Management app with AI-powered card management. Users register/sign in, manage multiple Kanban boards, drag-drop cards between columns, and chat with an AI that can create/edit/move cards.

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
  src/components/    # React components (KanbanBoard, BoardSelector, ChatSidebar, CardModal, etc.)
  src/lib/           # API client (api.ts), Kanban logic (kanban.ts)

backend/
  app/main.py        # FastAPI app factory, lifespan, static file mounts
  app/models.py      # Pydantic request/response models
  app/auth.py        # Password hashing (PBKDF2), session token generation
  app/dependencies.py # FastAPI dependencies (get_db, get_current_user_id)
  app/database.py    # SQLite schema and CRUD operations
  app/ai.py          # OpenRouter AI integration, response parsing
  app/routers/
    auth.py          # /api/login, /api/logout, /api/me, /api/register
    boards.py        # /api/boards CRUD + legacy /api/board
    cards.py         # /api/board/cards + /api/boards/{id}/cards
    columns.py       # /api/board/columns + /api/boards/{id}/columns
    ai.py            # /api/ai/chat, /api/ai/test + board-scoped AI
```

## Key Implementation Details

**ID Prefixing:** Column IDs use "col-" prefix, card IDs use "card-" prefix. The `parse_id()` function strips prefixes for DB queries. This prevents dnd-kit from confusing columns and cards.

**Auth:** Session-based authentication with PBKDF2 password hashing (stdlib, no extra deps). Sessions stored in DB with 30-day expiry. User registration with username validation (3-30 chars, alphanumeric/underscore) and min 8-char password. Legacy users with empty password_hash support "password" as credential.

**Database:** SQLite at `/app/data/kanban.db`. Schema: users, sessions, boards, columns, cards, labels. Multi-board per user. 5 default columns + 8 sample cards seeded on board creation. Cards support due_date and labels (comma-separated string) fields.

**Multi-Board:** Users can create/manage multiple boards. API supports both legacy single-board endpoints (`/api/board/*`) and new board-scoped endpoints (`/api/boards/{id}/*`). Frontend shows BoardSelector when no board is active.

**Frontend API Client:** `frontend/src/lib/api.ts` - all API calls use relative paths (no base URL needed since FastAPI serves everything).

**Optimistic Updates:** `KanbanBoard.tsx` updates local state immediately, then calls the API. On error it calls `loadBoard()` to re-sync from server.

**Labels:** Cards support comma-separated labels (e.g. "bug,feature,urgent"). Preset labels have color-coded badges (LabelPicker component). Custom labels also supported. Labels displayed on cards via CardLabels component.

**Search:** SearchBar in the board header filters cards across all columns by title, details, or labels text. Client-side filtering only.

**Board Title Editing:** Click the board title in the header to edit it inline. Saves via PUT /api/boards/{id}.

**AI Chat:** Board state sent as JSON context. AI returns `{"message": string, "board_updates": {...}}`. `_apply_board_updates()` in routers/ai.py resolves column titles to IDs so AI can reference columns by name. `parse_ai_response()` handles edge cases: unwraps nested responses (model sometimes wraps in `{"final":{...}}`), returns fallback message on empty `{}`.

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

- Backend: 88 pytest tests (auth, boards, cards, columns, labels, due dates, AI, multi-board)
- Frontend unit: 37 vitest tests (KanbanBoard, ChatSidebar, LoginForm, BoardSelector, SearchBar, CardLabels)
- E2E: 5 playwright tests

## Coding Standards

1. Use latest library versions and idiomatic approaches
2. Keep it simple - never over-engineer
3. Be concise - minimal documentation, no emojis
4. Always identify root cause before fixing (prove with evidence)
