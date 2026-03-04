# Code Review Report

## Summary

The codebase is well-structured for an MVP. The architecture is clean with clear separation between frontend and backend. All 65 tests pass (41 backend, 19 frontend unit, 5 E2E). The code follows the project's coding standards of simplicity and minimal documentation.

## Findings by Category

### Critical Issues

None identified. The codebase is functional and secure for MVP purposes.

### High Priority

**1. Database connection management in main.py**
- Location: `backend/app/main.py:76-85`, `205-210`
- Issue: `get_authenticated_user_id()` opens a new DB connection for every authenticated request, even before the endpoint opens its own connection. This doubles connection overhead.
- Action: Refactor to pass connection from endpoint to auth check, or use a request-scoped connection pattern.

**2. Unused `initialData` export in kanban.ts**
- Location: `frontend/src/lib/kanban.ts:18-72`
- Issue: The `initialData` constant and `createId` function are defined but never used since the app now fetches data from the API.
- Action: Remove dead code.

**3. Error string interpolation in JSON responses**
- Location: `backend/app/main.py:108`, `129`
- Issue: `f'{{"error":"{str(e)}"}}'` is vulnerable to JSON injection if the exception message contains quotes or special characters.
- Action: Use `json.dumps()` or return a proper dict that FastAPI serializes.

### Medium Priority

**4. Column rename fires on every keystroke**
- Location: `frontend/src/components/KanbanColumn.tsx:45`
- Issue: `onChange` calls `onRename` immediately, triggering an API call for each character typed.
- Action: Add debouncing or fire on blur instead.

**5. Missing error boundary for AI chat**
- Location: `frontend/src/components/ChatSidebar.tsx`
- Issue: If `sendChat` throws an unexpected error shape, the catch block may not handle it gracefully.
- Action: Consider a more robust error handling pattern or error boundary.

**6. Hardcoded credentials in source code**
- Location: `backend/app/main.py:26-28`
- Issue: `VALID_USERNAME`, `VALID_PASSWORD`, `SESSION_TOKEN` are hardcoded. This is documented as intentional for MVP but should be flagged for future work.
- Action: Document in CLAUDE.md that auth needs replacement for production.

**7. AI system prompt token usage**
- Location: `backend/app/ai.py:59`
- Issue: Full board JSON is included in every AI request. As boards grow, this could hit token limits.
- Action: Consider summarizing board state or truncating for large boards.

### Low Priority

**8. Inline SVG icons**
- Location: `frontend/src/components/KanbanCard.tsx:57-59`, `78-79`, `ChatSidebar.tsx:71-72`
- Issue: SVG icons are duplicated inline. Minor maintainability concern.
- Action: Extract to a shared Icons component if the codebase grows.

**9. Magic numbers in CSS**
- Location: `frontend/src/components/KanbanBoard.tsx:191-192`
- Issue: Gradient sizes (420px, 520px) are magic numbers.
- Action: Document or extract to CSS variables if design system expands.

**10. Inconsistent error return patterns**
- Location: `backend/app/main.py`
- Issue: Some endpoints return `Response(status_code=...)` while others rely on FastAPI's automatic handling. Mixed patterns.
- Action: Standardize on either HTTPException or custom Response objects.

**11. Test deprecation warnings**
- Location: `backend/tests/test_board.py`, `test_main.py`
- Issue: httpx cookie deprecation warnings in test output.
- Action: Update test fixtures to use client-level cookies per httpx migration guide.

### Code Quality Observations

**Positive:**
- Clean component composition in React
- Good use of TypeScript types throughout
- Optimistic updates with rollback pattern
- Comprehensive test coverage for critical paths
- Clear separation of concerns (api.ts, kanban.ts, components)
- Proper use of `useCallback` to prevent unnecessary re-renders
- AI response parsing handles edge cases gracefully

**Areas for future improvement:**
- Consider React Query or SWR for data fetching to get caching, refetching, and loading states for free
- Add request ID logging for debugging production issues
- Consider adding health check for database connectivity

## Test Coverage Analysis

| Area | Coverage | Notes |
|------|----------|-------|
| Auth endpoints | Good | Login, logout, session validation |
| Board CRUD | Good | All operations covered with error cases |
| AI integration | Good | Mocked tests for all update types |
| Frontend components | Good | Key interactions tested |
| E2E flows | Adequate | Core happy paths covered |

**Gaps:**
- No tests for concurrent database operations
- No tests for AI rate limiting or timeout handling
- No tests for board with many cards (performance)

## Security Considerations

For MVP, security is acceptable. For production:

1. Replace hardcoded auth with proper authentication (OAuth, JWT)
2. Add rate limiting on AI endpoints
3. Sanitize AI responses before applying board updates
4. Add CSRF protection
5. Consider input length limits on card titles/details

## Recommended Actions

### Immediate (before next feature work)
1. Fix JSON injection in error responses
2. Remove unused `initialData` code
3. Add debouncing to column rename

### Short-term
4. Refactor DB connection handling
5. Fix httpx deprecation warnings in tests
6. Standardize error response patterns

### Before production
7. Replace auth system
8. Add rate limiting
9. Implement proper logging
10. Add monitoring/alerting