import type { BoardData } from "@/lib/kanban";

const headers = { "Content-Type": "application/json" };

export async function fetchBoard(): Promise<BoardData> {
  const resp = await fetch("/api/board");
  if (!resp.ok) throw new Error("Failed to load board");
  return resp.json();
}

export async function renameColumn(columnId: string, title: string): Promise<void> {
  const resp = await fetch(`/api/board/columns/${columnId}`, {
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
): Promise<{ id: string; title: string; details: string }> {
  const resp = await fetch("/api/board/cards", {
    method: "POST",
    headers,
    body: JSON.stringify({ column_id: columnId, title, details }),
  });
  if (!resp.ok) throw new Error("Failed to create card");
  return resp.json();
}

export async function updateCard(
  cardId: string,
  title: string,
  details: string,
): Promise<void> {
  const resp = await fetch(`/api/board/cards/${cardId}`, {
    method: "PUT",
    headers,
    body: JSON.stringify({ title, details }),
  });
  if (!resp.ok) throw new Error("Failed to update card");
}

export async function deleteCard(cardId: string): Promise<void> {
  const resp = await fetch(`/api/board/cards/${cardId}`, { method: "DELETE" });
  if (!resp.ok) throw new Error("Failed to delete card");
}

export async function moveCardApi(
  cardId: string,
  columnId: string,
  position: number,
): Promise<void> {
  const resp = await fetch(`/api/board/cards/${cardId}/move`, {
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
): Promise<ChatResponse> {
  const resp = await fetch("/api/ai/chat", {
    method: "POST",
    headers,
    body: JSON.stringify({ message, history }),
  });
  if (!resp.ok) throw new Error("Failed to send message");
  return resp.json();
}
