"use client";

import { useCallback, useEffect, useState } from "react";
import type { BoardSummary } from "@/lib/kanban";
import { fetchBoards, createBoard, deleteBoard } from "@/lib/api";

type BoardSelectorProps = {
  onSelectBoard: (boardId: number) => void;
  onLogout: () => void;
  username: string;
};

export const BoardSelector = ({ onSelectBoard, onLogout, username }: BoardSelectorProps) => {
  const [boards, setBoards] = useState<BoardSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");

  const loadBoards = useCallback(async () => {
    try {
      const data = await fetchBoards();
      setBoards(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBoards();
  }, [loadBoards]);

  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    setCreating(true);
    try {
      const board = await createBoard(newTitle.trim());
      setNewTitle("");
      if (board.id) {
        onSelectBoard(board.id);
      } else {
        loadBoards();
      }
    } catch {
      // ignore
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (boardId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (boards.length <= 1) return;
    try {
      await deleteBoard(boardId);
      loadBoards();
    } catch {
      // ignore
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-[var(--gray-text)]">Loading boards...</p>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-[var(--surface)]">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <div className="relative mx-auto max-w-2xl px-5 py-10">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="h-2.5 w-2.5 rounded-full bg-[var(--accent-yellow)]" />
            <h1 className="font-display text-xl font-semibold text-[var(--navy-dark)]">
              Kanban Studio
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--navy-dark)] text-[10px] font-bold uppercase text-white">
              {username.charAt(0)}
            </div>
            <span className="text-xs font-semibold text-[var(--gray-text)]">{username}</span>
            <button
              type="button"
              onClick={onLogout}
              className="ml-2 rounded-lg p-1.5 text-[var(--gray-text)] transition hover:bg-[var(--navy-dark)]/5 hover:text-[var(--navy-dark)]"
              aria-label="Sign out"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4.5 w-4.5">
                <path fillRule="evenodd" d="M3 4.25A2.25 2.25 0 015.25 2h5.5A2.25 2.25 0 0113 4.25v2a.75.75 0 01-1.5 0v-2a.75.75 0 00-.75-.75h-5.5a.75.75 0 00-.75.75v11.5c0 .414.336.75.75.75h5.5a.75.75 0 00.75-.75v-2a.75.75 0 011.5 0v2A2.25 2.25 0 0110.75 18h-5.5A2.25 2.25 0 013 15.75V4.25z" clipRule="evenodd" />
                <path fillRule="evenodd" d="M19 10a.75.75 0 00-.75-.75H8.704l1.048-.943a.75.75 0 10-1.004-1.114l-2.5 2.25a.75.75 0 000 1.114l2.5 2.25a.75.75 0 101.004-1.114l-1.048-.943h9.546A.75.75 0 0019 10z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </header>

        <div className="mt-8">
          <h2 className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
            Your Boards
          </h2>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {boards.map((board) => (
              <button
                key={board.id}
                type="button"
                onClick={() => onSelectBoard(board.id)}
                className="group relative rounded-2xl border border-[var(--stroke)] bg-white p-5 text-left shadow-[var(--shadow)] transition hover:border-[var(--primary-blue)] hover:shadow-md"
              >
                <h3 className="font-display text-base font-semibold text-[var(--navy-dark)]">
                  {board.title}
                </h3>
                <p className="mt-1 text-xs text-[var(--gray-text)]">
                  {board.column_count ?? 0} columns &middot; {board.card_count ?? 0} cards
                </p>
                <p className="mt-0.5 text-[10px] text-[var(--gray-text)]/60">
                  Created {new Date(board.created_at).toLocaleDateString()}
                </p>
                {boards.length > 1 && (
                  <button
                    type="button"
                    onClick={(e) => handleDelete(board.id, e)}
                    className="absolute right-3 top-3 rounded-lg p-1 text-[var(--gray-text)] opacity-0 transition hover:bg-red-50 hover:text-red-500 group-hover:opacity-100"
                    aria-label="Delete board"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                      <path fillRule="evenodd" d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 10.23 1.482l.149-.022.841 10.518A2.75 2.75 0 007.596 19h4.807a2.75 2.75 0 002.742-2.53l.841-10.52.149.023a.75.75 0 00.23-1.482A41.03 41.03 0 0014 4.193V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4zM8.58 7.72a.75.75 0 00-1.5.06l.3 7.5a.75.75 0 101.5-.06l-.3-7.5zm4.34.06a.75.75 0 10-1.5-.06l-.3 7.5a.75.75 0 101.5.06l.3-7.5z" clipRule="evenodd" />
                    </svg>
                  </button>
                )}
              </button>
            ))}

            <div className="rounded-2xl border-2 border-dashed border-[var(--stroke)] p-5">
              <h3 className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
                New Board
              </h3>
              <div className="mt-3 flex gap-2">
                <input
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                  placeholder="Board name"
                  className="flex-1 rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm font-medium text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)] placeholder:text-[var(--gray-text)]/40"
                />
                <button
                  type="button"
                  onClick={handleCreate}
                  disabled={creating || !newTitle.trim()}
                  className="rounded-xl bg-[var(--primary-blue)] px-4 py-2 text-xs font-semibold uppercase text-white transition hover:brightness-110 disabled:opacity-60"
                >
                  {creating ? "..." : "Create"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
