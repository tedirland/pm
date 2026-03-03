# Frontend -- Existing Code

## Overview

A standalone Next.js 16 Kanban board demo. All state is in-memory (React useState). No backend, no auth, no persistence. Uses Tailwind CSS v4, dnd-kit for drag-and-drop, and the project color scheme defined in CSS custom properties.

## Tech Stack

- Next.js 16.1.6, React 19.2.3, TypeScript 5
- Tailwind CSS 4 (via @tailwindcss/postcss)
- dnd-kit (core 6.3, sortable 10.0) for drag-and-drop
- clsx for conditional class names
- Fonts: Space Grotesk (display), Manrope (body) via next/font/google

## Project Structure

### src/app/
- `layout.tsx` -- Root layout. Loads fonts, sets metadata (title: "Kanban Studio").
- `page.tsx` -- Renders `<KanbanBoard />` as the sole page content.
- `globals.css` -- CSS custom properties for the color scheme, Tailwind import, base styles.

### src/components/
- `KanbanBoard.tsx` -- Main board component. Manages all board state (columns, cards) via useState. Handles drag-and-drop context, column rename, card add, card delete. Renders header with column summary pills and a 5-column grid of KanbanColumn components.
- `KanbanColumn.tsx` -- Single column with droppable zone, editable title input, card list (SortableContext), empty-state placeholder, and NewCardForm.
- `KanbanCard.tsx` -- Sortable card with title, details, and a "Remove" button. Uses useSortable from dnd-kit.
- `KanbanCardPreview.tsx` -- Lightweight card clone shown in DragOverlay (no interactivity).
- `NewCardForm.tsx` -- Expandable form at the bottom of each column. Toggle open/close, title (required) + details fields, submit/cancel buttons.

### src/lib/
- `kanban.ts` -- Types (Card, Column, BoardData), initial demo data (5 columns, 8 cards), `moveCard()` logic for same-column reorder and cross-column moves, `createId()` helper.

### src/test/
- `setup.ts` -- Imports @testing-library/jest-dom matchers.

## Tests

### Unit tests (Vitest + React Testing Library)
- `src/components/KanbanBoard.test.tsx` -- Renders 5 columns, renames a column, adds and removes a card.
- `src/lib/kanban.test.ts` -- Tests moveCard for same-column reorder, cross-column move, and drop-on-column-end.

### E2E tests (Playwright, Chromium only)
- `tests/kanban.spec.ts` -- Loads board, adds a card, drags a card between columns.

## Scripts (package.json)
- `dev` -- next dev
- `build` -- next build
- `test` / `test:unit` -- vitest run
- `test:e2e` -- playwright test
- `test:all` -- unit + e2e

## Key Types (from src/lib/kanban.ts)
- `Card { id, title, details }`
- `Column { id, title, cardIds }`
- `BoardData { columns: Column[], cards: Record<string, Card> }`

## Color Scheme (from globals.css)
- `--accent-yellow: #ecad0a`
- `--primary-blue: #209dd7`
- `--secondary-purple: #753991`
- `--navy-dark: #032147`
- `--gray-text: #888888`
- `--surface: #f7f8fb`
- `--surface-strong: #ffffff`

## Notes
- next.config.ts is empty (no static export configured yet).
- Playwright config expects dev server on 127.0.0.1:3000.
- No API calls exist yet; all data is hardcoded in kanban.ts initialData.
