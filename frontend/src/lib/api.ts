import type { BoardData, BoardSummary } from "@/lib/kanban";

const headers = { "Content-Type": "application/json" };

// --- Auth ---

export async function register(
  username: string,
  password: string
): Promise<{ username: string }> {
  const resp = await fetch("/api/register", {
    method: "POST",
    headers,
    body: JSON.stringify({ username, password }),
  });
  if (!resp.ok) {
    const data = await resp.json();
    throw new Error(data.detail || "Registration failed");
  }
  return resp.json();
}

// --- Board list ---

export async function fetchBoards(): Promise<BoardSummary[]> {
  const resp = await fetch("/api/boards");
  if (!resp.ok) throw new Error("Failed to load boards");
  return resp.json();
}

export async function createBoard(title: string): Promise<BoardData> {
  const resp = await fetch("/api/boards", {
    method: "POST",
    headers,
    body: JSON.stringify({ title }),
  });
  if (!resp.ok) throw new Error("Failed to create board");
  return resp.json();
}

export async function deleteBoard(boardId: number): Promise<void> {
  const resp = await fetch(`/api/boards/${boardId}`, { method: "DELETE" });
  if (!resp.ok) throw new Error("Failed to delete board");
}

export async function updateBoardTitle(boardId: number, title: string): Promise<void> {
  const resp = await fetch(`/api/boards/${boardId}`, {
    method: "PUT",
    headers,
    body: JSON.stringify({ title }),
  });
  if (!resp.ok) throw new Error("Failed to update board");
}

// --- Legacy single-board (backward compat) ---

export async function fetchBoard(): Promise<BoardData> {
  const resp = await fetch("/api/board");
  if (!resp.ok) throw new Error("Failed to load board");
  return resp.json();
}

// --- Board-scoped operations ---

export async function fetchBoardById(boardId: number): Promise<BoardData> {
  const resp = await fetch(`/api/boards/${boardId}`);
  if (!resp.ok) throw new Error("Failed to load board");
  return resp.json();
}

export async function addColumn(title: string, boardId?: number): Promise<{ id: string; title: string }> {
  const url = boardId ? `/api/boards/${boardId}/columns` : "/api/board/columns";
  const resp = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({ title }),
  });
  if (!resp.ok) throw new Error("Failed to add column");
  return resp.json();
}

export async function deleteColumn(columnId: string, boardId?: number): Promise<void> {
  const url = boardId ? `/api/boards/${boardId}/columns/${columnId}` : `/api/board/columns/${columnId}`;
  const resp = await fetch(url, { method: "DELETE" });
  if (!resp.ok) throw new Error("Failed to delete column");
}

export async function renameColumn(columnId: string, title: string, boardId?: number): Promise<void> {
  const url = boardId ? `/api/boards/${boardId}/columns/${columnId}` : `/api/board/columns/${columnId}`;
  const resp = await fetch(url, {
    method: "PUT",
    headers,
    body: JSON.stringify({ title }),
  });
  if (!resp.ok) throw new Error("Failed to rename column");
}

export async function createCard(
  columnId: string,
  title: string,
  details: string,
  dueDate?: string | null,
  boardId?: number,
): Promise<{ id: string; title: string; details: string; due_date?: string | null; labels?: string }> {
  const url = boardId ? `/api/boards/${boardId}/cards` : "/api/board/cards";
  const resp = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({ column_id: columnId, title, details, due_date: dueDate || null }),
  });
  if (!resp.ok) throw new Error("Failed to create card");
  return resp.json();
}

export async function updateCard(
  cardId: string,
  title: string,
  details: string,
  dueDate?: string | null,
  labels?: string,
  boardId?: number,
): Promise<void> {
  const url = boardId ? `/api/boards/${boardId}/cards/${cardId}` : `/api/board/cards/${cardId}`;
  const resp = await fetch(url, {
    method: "PUT",
    headers,
    body: JSON.stringify({ title, details, due_date: dueDate || null, labels: labels ?? null }),
  });
  if (!resp.ok) throw new Error("Failed to update card");
}

export async function deleteCard(cardId: string, boardId?: number): Promise<void> {
  const url = boardId ? `/api/boards/${boardId}/cards/${cardId}` : `/api/board/cards/${cardId}`;
  const resp = await fetch(url, { method: "DELETE" });
  if (!resp.ok) throw new Error("Failed to delete card");
}

export async function moveCardApi(
  cardId: string,
  columnId: string,
  position: number,
  boardId?: number,
): Promise<void> {
  const url = boardId ? `/api/boards/${boardId}/cards/${cardId}/move` : `/api/board/cards/${cardId}/move`;
  const resp = await fetch(url, {
    method: "PUT",
    headers,
    body: JSON.stringify({ column_id: columnId, position }),
  });
  if (!resp.ok) throw new Error("Failed to move card");
}

export type ChatMessage = { role: "user" | "assistant"; content: string };

export type ChatResponse = { message: string; board_updated: boolean };

export async function sendChat(
  message: string,
  history: ChatMessage[],
  boardId?: number,
): Promise<ChatResponse> {
  const url = boardId ? `/api/boards/${boardId}/ai/chat` : "/api/ai/chat";
  const resp = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({ message, history }),
  });
  if (!resp.ok) throw new Error("Failed to send message");
  return resp.json();
}
