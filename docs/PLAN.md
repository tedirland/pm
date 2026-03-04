# High level steps for project

## Design decisions

- Auth: simple cookie-based flag, no JWT. Hardcoded "user"/"password". Keep it trivial but structured so real auth can replace it later.
- Frontend: statically exported Next.js SPA served by FastAPI. No SSR / Next.js API routes.
- AI conversation history: in-memory (React state), not persisted. Lost on refresh.
- Docker volume: SQLite db file mounted as a volume so data survives container restarts.
- Scripts: simple wrappers around docker build/run/stop.

---

## Part 1: Plan

- [x] Enrich PLAN.md with detailed substeps, checklists, tests, and success criteria
- [x] Create frontend/AGENTS.md describing the existing frontend code
- [x] User approves the plan

Success: User confirms plan is good to proceed.

---

## Part 2: Scaffolding

Set up Docker, FastAPI backend, and start/stop scripts. Serve a hello-world page and expose a test API endpoint.

- [x] Create `backend/pyproject.toml` with FastAPI, uvicorn dependencies (managed by uv)
- [x] Create `backend/app/main.py` with a FastAPI app that:
  - Serves a static "Hello World" HTML page at GET /
  - Has a GET /api/health endpoint returning `{"status": "ok"}`
- [x] Create `Dockerfile` in project root:
  - Based on a Python image with uv
  - Install backend dependencies with uv
  - Expose port 8000
  - Run uvicorn
- [x] Create `scripts/start.sh` (Mac/Linux) -- builds and runs the Docker container, mounts a volume for the SQLite db
- [x] Create `scripts/stop.sh` (Mac/Linux) -- stops and removes the container
- [x] Create `scripts/start.bat` and `scripts/stop.bat` (Windows equivalents)
- [x] Update `backend/AGENTS.md` with backend structure description

Tests and success criteria:
- [x] `docker build` completes without errors
- [x] `scripts/start.sh` starts the container; curl http://localhost:8000/ returns "Hello World" HTML
- [x] curl http://localhost:8000/api/health returns `{"status": "ok"}`
- [x] `scripts/stop.sh` stops the container cleanly
- [x] Backend unit test: test /api/health returns 200 with expected JSON (pytest + httpx)

---

## Part 3: Add in Frontend

Statically build the Next.js frontend and serve it via FastAPI at /.

- [x] Add `output: "export"` to `frontend/next.config.ts`
- [x] Adjust layout.tsx if needed (remove features incompatible with static export)
- [x] Update Dockerfile to: install Node.js, run `npm ci && npm run build` in frontend/, copy the static output to a location FastAPI serves
- [x] Update `backend/app/main.py` to serve the static frontend files at / (using StaticFiles mount or similar)
- [x] Ensure client-side routing works (fallback to index.html)

Tests and success criteria:
- [x] `npm run build` in frontend/ succeeds with static export
- [x] Frontend unit tests still pass (`npm run test:unit`)
- [x] Docker build completes; visiting http://localhost:8000/ shows the Kanban board
- [x] All existing Kanban interactions work (rename column, add card, delete card, drag-and-drop)

---

## Part 4: Fake User Sign In

Add a login screen. Hardcoded credentials: "user" / "password".

- [x] Add POST /api/login endpoint: accepts `{username, password}`, validates against hardcoded values, sets a session cookie on success
- [x] Add POST /api/logout endpoint: clears the session cookie
- [x] Add GET /api/me endpoint: returns the current user if the cookie is valid, 401 otherwise
- [x] Add a login page/component in the frontend (simple form, username + password fields, submit button, error message on failure)
- [x] Gate the Kanban board behind auth: if not logged in, show login; if logged in, show board + logout button
- [x] Style login page using the project color scheme

Tests and success criteria:
- [x] Backend unit tests: login with correct creds returns 200 + cookie; wrong creds returns 401; /api/me with valid cookie returns user; /api/me without cookie returns 401; logout clears cookie
- [x] Frontend unit tests: login form renders, submits, shows error on failure
- [x] E2E: full login -> see board -> logout -> see login flow
- [x] Visiting / without auth shows login page

---

## Part 5: Database Modeling

Design and document the SQLite schema for Kanban persistence.

- [x] Create `docs/SCHEMA.md` with the proposed database schema including tables, columns, types, relationships
- [x] Proposed tables: users, boards, columns, cards (with position/ordering fields)
- [x] Save the schema also as `docs/schema.json` (machine-readable)
- [x] Get user sign-off on the schema

Tests and success criteria:
- [x] Schema supports: multiple users, one board per user (extensible to many), ordered columns, ordered cards within columns, card title + details
- [x] User approves the schema

---

## Part 6: Backend API

Implement CRUD API routes for the Kanban board backed by SQLite.

- [x] Create database module (`backend/app/database.py`): SQLite connection, create tables if not exist on startup
- [x] Seed default board data for new users on first login
- [x] API endpoints:
  - GET /api/board -- returns the full board (columns + cards) for the logged-in user
  - PUT /api/board/columns/:id -- rename a column
  - POST /api/board/cards -- create a card in a column
  - PUT /api/board/cards/:id -- update a card (title, details)
  - DELETE /api/board/cards/:id -- delete a card
  - PUT /api/board/cards/:id/move -- move a card (change column and/or position)
- [x] All endpoints require auth (valid session cookie)

Tests and success criteria:
- [x] Pytest tests for every endpoint (happy path + error cases)
- [x] Database is created automatically if it does not exist
- [x] Data persists across container restarts (Docker volume)
- [x] Card ordering is maintained correctly after moves

---

## Part 7: Frontend + Backend Integration

Connect the frontend to the backend API so the Kanban board is persistent.

- [x] Replace in-memory useState board state with API calls:
  - Fetch board on mount (GET /api/board)
  - Rename column calls PUT /api/board/columns/:id
  - Add card calls POST /api/board/cards
  - Delete card calls DELETE /api/board/cards/:id
  - Drag-and-drop calls PUT /api/board/cards/:id/move
- [x] Add loading and error states to the UI
- [x] Configure frontend API base URL (relative paths since FastAPI serves everything)

Tests and success criteria:
- [x] Frontend unit tests: mock API calls, verify correct requests are made
- [x] E2E tests: login, see board from DB, add card, refresh page, card persists
- [x] Drag-and-drop updates persist across page reload
- [x] Column renames persist across page reload

---

## Handoff Notes

Key implementation details for the next agent:

- **ID prefixing**: Column IDs are prefixed `col-` and card IDs `card-` in API responses (e.g. `"col-1"`, `"card-3"`). This prevents dnd-kit from confusing columns and cards when they share the same integer ID. `parse_id()` in `main.py` strips the prefix before DB queries.
- **Auth**: Hardcoded `SESSION_TOKEN = "valid-session"` cookie. `get_authenticated_user_id()` in `main.py` validates session and auto-creates user/board via `ensure_user()`/`ensure_board()`.
- **Frontend API client**: `frontend/src/lib/api.ts` — all API calls use relative paths (no base URL needed since FastAPI serves everything).
- **Optimistic updates**: `KanbanBoard.tsx` updates local state immediately, then calls the API. On error it calls `loadBoard()` to re-sync from server.
- **Docker**: `scripts/start.sh` does `docker rm -f` before `docker run` to avoid stale containers. Volume mounts `./data:/app/data` for SQLite persistence. Use `--no-cache` on rebuild if frontend changes aren't appearing.
- **OpenRouter config**: `.env` has `OPENROUTER_API_KEY`. Model is `openai/gpt-oss-120b`. The `.env` file needs to be passed into the Docker container (not yet implemented — Part 8 needs this).
- **Test counts**: 26 backend (pytest), 12 frontend unit (vitest), 5 e2e (playwright) = 43 total, all passing.
- **UI components**: `CardModal` handles both create and edit. `KanbanCard` has two-click delete confirmation. Workload overview bar shows per-column card counts between header and board.

---

## Part 8: AI Connectivity

Connect the backend to OpenRouter and verify it works.

- [x] Add openai Python package to backend dependencies
- [x] Create `backend/app/ai.py` module: configure OpenAI client with OpenRouter base URL and OPENROUTER_API_KEY from environment
- [x] Add GET /api/ai/test endpoint that sends a simple "What is 2+2?" prompt and returns the AI response
- [x] Load .env file in the backend (or pass through Docker)

Tests and success criteria:
- [x] /api/ai/test returns a response containing "4"
- [x] Backend unit test with mocked OpenAI client verifies the call structure
- [x] OPENROUTER_API_KEY is never logged or exposed in responses

---

## Part 9: AI Structured Outputs

Extend the AI endpoint to accept user questions with board context and return structured responses that can optionally modify the board.

- [x] Define the structured output schema: `{ message: string, board_updates?: { cards_to_create?, cards_to_update?, cards_to_delete?, cards_to_move? } }`
- [x] Add POST /api/ai/chat endpoint:
  - Accepts `{ message: string, history: [{role, content}] }`
  - Sends to AI: system prompt with board JSON + user message + history
  - Parses structured output
  - If board_updates present, applies them to the database
  - Returns the AI message + whether the board was updated
- [x] System prompt instructs the AI on the board structure and available actions

Tests and success criteria:
- [x] Backend unit tests with mocked AI: verify board context is sent, structured output is parsed, board updates are applied
- [x] Test: AI response without board updates returns message only
- [x] Test: AI response with card creation actually creates the card in the DB
- [x] Test: malformed AI output is handled gracefully

---

## Part 10: AI Chat Sidebar

Add a sidebar chat widget to the frontend that communicates with the AI and auto-refreshes the board.

- [ ] Create ChatSidebar component: collapsible panel on the right side, message list, input field, send button
- [ ] Maintain conversation history in React state (array of {role, content})
- [ ] On send: POST /api/ai/chat with message + history
- [ ] Display AI response in the chat
- [ ] If the AI updated the board, re-fetch the board data to reflect changes
- [ ] Style the sidebar using the project color scheme (subtle, does not overwhelm the board)
- [ ] Add a toggle button to open/close the sidebar

Tests and success criteria:
- [ ] Frontend unit tests: sidebar renders, sends messages, displays responses
- [ ] E2E test: open sidebar, send a message like "Create a card called Test in Backlog", verify the card appears on the board
- [ ] Conversation history is maintained within the session
- [ ] Sidebar is responsive and does not break the board layout