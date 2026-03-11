"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { CardModal } from "@/components/CardModal";
import { ChatPanel } from "@/components/ChatPanel";
import { SearchBar } from "@/components/SearchBar";
import { moveCard, type BoardData } from "@/lib/kanban";
import {
  fetchBoard,
  fetchBoardById,
  updateBoardTitle,
  addColumn as addColumnApi,
  deleteColumn as deleteColumnApi,
  renameColumn as renameColumnApi,
  createCard as createCardApi,
  updateCard as updateCardApi,
  deleteCard as deleteCardApi,
  moveCardApi,
} from "@/lib/api";

type ModalState =
  | { mode: "create"; columnId: string }
  | { mode: "edit"; cardId: string }
  | null;

type KanbanBoardProps = {
  username?: string;
  boardId?: number;
  onLogout?: () => void;
  onBackToBoards?: () => void;
};

export const KanbanBoard = ({ username, boardId, onLogout, onBackToBoards }: KanbanBoardProps) => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [modal, setModal] = useState<ModalState>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [editingTitle, setEditingTitle] = useState(false);
  const [localTitle, setLocalTitle] = useState("");
  const titleInputRef = useRef<HTMLInputElement>(null);

  const loadBoard = useCallback(async () => {
    try {
      const data = boardId ? await fetchBoardById(boardId) : await fetchBoard();
      setBoard(data);
      setLocalTitle(data.title || "Kanban Studio");
      setError(null);
    } catch {
      setError("Failed to load board");
    } finally {
      setLoading(false);
    }
  }, [boardId]);

  useEffect(() => {
    loadBoard();
  }, [loadBoard]);

  useEffect(() => {
    if (editingTitle) titleInputRef.current?.select();
  }, [editingTitle]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const handleTitleSave = () => {
    setEditingTitle(false);
    const trimmed = localTitle.trim();
    if (!trimmed || !boardId) return;
    setBoard((prev) => prev ? { ...prev, title: trimmed } : prev);
    updateBoardTitle(boardId, trimmed).catch(() => loadBoard());
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id || !board) return;

    const newColumns = moveCard(board.columns, active.id as string, over.id as string);
    setBoard((prev) => prev ? { ...prev, columns: newColumns } : prev);

    const cardId = active.id as string;
    for (const col of newColumns) {
      const idx = col.cardIds.indexOf(cardId);
      if (idx !== -1) {
        moveCardApi(cardId, col.id, idx, boardId).catch(() => loadBoard());
        break;
      }
    }
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    setBoard((prev) =>
      prev
        ? {
            ...prev,
            columns: prev.columns.map((column) =>
              column.id === columnId ? { ...column, title } : column
            ),
          }
        : prev
    );
    renameColumnApi(columnId, title, boardId).catch(() => loadBoard());
  };

  const handleAddColumn = async () => {
    try {
      const col = await addColumnApi("New Column", boardId);
      setBoard((prev) =>
        prev
          ? {
              ...prev,
              columns: [...prev.columns, { id: col.id, title: col.title, cardIds: [] }],
            }
          : prev
      );
    } catch {
      setError("Failed to add column");
    }
  };

  const handleDeleteColumn = async (columnId: string) => {
    setBoard((prev) =>
      prev
        ? {
            ...prev,
            columns: prev.columns.filter((c) => c.id !== columnId),
            cards: Object.fromEntries(
              Object.entries(prev.cards).filter(
                ([id]) => !prev.columns.find((c) => c.id === columnId)?.cardIds.includes(id)
              )
            ),
          }
        : prev
    );
    try {
      await deleteColumnApi(columnId, boardId);
    } catch {
      loadBoard();
    }
  };

  const handleAddCard = async (columnId: string, title: string, details: string, dueDate?: string | null) => {
    try {
      const card = await createCardApi(columnId, title, details, dueDate, boardId);
      setBoard((prev) =>
        prev
          ? {
              ...prev,
              cards: { ...prev.cards, [card.id]: card },
              columns: prev.columns.map((column) =>
                column.id === columnId
                  ? { ...column, cardIds: [...column.cardIds, card.id] }
                  : column
              ),
            }
          : prev
      );
    } catch {
      setError("Failed to create card");
    }
  };

  const handleEditCard = async (cardId: string, title: string, details: string, dueDate?: string | null, labels?: string) => {
    setBoard((prev) =>
      prev
        ? {
            ...prev,
            cards: {
              ...prev.cards,
              [cardId]: { ...prev.cards[cardId], title, details, due_date: dueDate, labels },
            },
          }
        : prev
    );
    try {
      await updateCardApi(cardId, title, details, dueDate, labels, boardId);
    } catch {
      loadBoard();
    }
  };

  const handleDeleteCard = async (columnId: string, cardId: string) => {
    setBoard((prev) =>
      prev
        ? {
            ...prev,
            cards: Object.fromEntries(
              Object.entries(prev.cards).filter(([id]) => id !== cardId)
            ),
            columns: prev.columns.map((column) =>
              column.id === columnId
                ? { ...column, cardIds: column.cardIds.filter((id) => id !== cardId) }
                : column
            ),
          }
        : prev
    );
    try {
      await deleteCardApi(cardId, boardId);
    } catch {
      loadBoard();
    }
  };

  // Filter cards by search query
  const getFilteredCardIds = (cardIds: string[]) => {
    if (!searchQuery.trim()) return cardIds;
    const q = searchQuery.toLowerCase();
    return cardIds.filter((id) => {
      const card = board?.cards[id];
      if (!card) return false;
      return (
        card.title.toLowerCase().includes(q) ||
        card.details.toLowerCase().includes(q) ||
        (card.labels && card.labels.toLowerCase().includes(q))
      );
    });
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-[var(--gray-text)]">Loading board...</p>
      </div>
    );
  }

  if (error && !board) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (!board) return null;

  const activeCard = activeCardId ? board.cards[activeCardId] : null;

  return (
    <div className="relative flex h-dvh flex-col overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      {/* Header */}
      <header className="relative z-10 mx-5 mt-5 shrink-0 flex items-center justify-between rounded-2xl border border-[var(--stroke)] bg-white/80 px-5 py-2.5 shadow-[var(--shadow)] backdrop-blur">
        <div className="flex items-center gap-3">
          {onBackToBoards && (
            <button
              type="button"
              onClick={onBackToBoards}
              className="rounded-lg p-1.5 text-[var(--gray-text)] transition hover:bg-[var(--navy-dark)]/5 hover:text-[var(--navy-dark)]"
              aria-label="Back to boards"
              title="Back to boards"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4.5 w-4.5">
                <path fillRule="evenodd" d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z" clipRule="evenodd" />
              </svg>
            </button>
          )}
          <span className="h-2.5 w-2.5 rounded-full bg-[var(--accent-yellow)]" />
          {editingTitle ? (
            <input
              ref={titleInputRef}
              value={localTitle}
              onChange={(e) => setLocalTitle(e.target.value)}
              onBlur={handleTitleSave}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleTitleSave();
                if (e.key === "Escape") {
                  setLocalTitle(board.title || "Kanban Studio");
                  setEditingTitle(false);
                }
              }}
              className="font-display text-xl font-semibold text-[var(--navy-dark)] bg-transparent border-b-2 border-[var(--primary-blue)] outline-none"
              aria-label="Edit board title"
            />
          ) : (
            <h1
              className="font-display text-xl font-semibold text-[var(--navy-dark)] cursor-pointer hover:text-[var(--primary-blue)] transition"
              onClick={() => {
                if (boardId) {
                  setLocalTitle(board.title || "Kanban Studio");
                  setEditingTitle(true);
                }
              }}
              title={boardId ? "Click to rename" : undefined}
            >
              {board?.title || "Kanban Studio"}
            </h1>
          )}
        </div>
        <div className="flex items-center gap-3">
          <SearchBar value={searchQuery} onChange={setSearchQuery} />
          {username && onLogout && (
            <>
              <div className="mx-1 h-4 w-px bg-[var(--stroke)]" />
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--navy-dark)] text-[10px] font-bold uppercase text-white">
                {username.charAt(0)}
              </div>
              <span className="text-xs font-semibold text-[var(--gray-text)]">
                {username}
              </span>
              <button
                type="button"
                onClick={() => setChatOpen(!chatOpen)}
                className={`rounded-lg p-1.5 transition ${
                  chatOpen
                    ? "bg-[var(--secondary-purple)]/15 text-[var(--secondary-purple)]"
                    : "text-[var(--secondary-purple)] hover:bg-[var(--secondary-purple)]/10"
                }`}
                aria-label="AI Chat"
                title="AI Chat"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4.5 w-4.5">
                  <path fillRule="evenodd" d="M3.43 2.524A41.29 41.29 0 0110 2c2.236 0 4.43.18 6.57.524 1.437.231 2.43 1.49 2.43 2.902v5.148c0 1.413-.993 2.67-2.43 2.902a41.102 41.102 0 01-3.55.414c-.28.02-.521.18-.643.413l-1.712 3.293a.75.75 0 01-1.33 0l-1.713-3.293a.783.783 0 00-.642-.413 41.108 41.108 0 01-3.55-.414C1.993 13.245 1 11.986 1 10.574V5.426c0-1.413.993-2.67 2.43-2.902z" clipRule="evenodd" />
                </svg>
              </button>
              <button
                type="button"
                onClick={onLogout}
                className="rounded-lg p-1.5 text-[var(--gray-text)] transition hover:bg-[var(--navy-dark)]/5 hover:text-[var(--navy-dark)]"
                aria-label="Sign out"
                title="Sign out"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4.5 w-4.5">
                  <path fillRule="evenodd" d="M3 4.25A2.25 2.25 0 015.25 2h5.5A2.25 2.25 0 0113 4.25v2a.75.75 0 01-1.5 0v-2a.75.75 0 00-.75-.75h-5.5a.75.75 0 00-.75.75v11.5c0 .414.336.75.75.75h5.5a.75.75 0 00.75-.75v-2a.75.75 0 011.5 0v2A2.25 2.25 0 0110.75 18h-5.5A2.25 2.25 0 013 15.75V4.25z" clipRule="evenodd" />
                  <path fillRule="evenodd" d="M19 10a.75.75 0 00-.75-.75H8.704l1.048-.943a.75.75 0 10-1.004-1.114l-2.5 2.25a.75.75 0 000 1.114l2.5 2.25a.75.75 0 101.004-1.114l-1.048-.943h9.546A.75.75 0 0019 10z" clipRule="evenodd" />
                </svg>
              </button>
            </>
          )}
        </div>
      </header>

      {/* Board + Chat layout */}
      <div className="relative flex min-h-0 flex-1 gap-5 overflow-hidden px-5 pb-5 pt-5">
        {/* Board columns */}
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <section className="flex min-w-0 flex-1 items-start gap-4 overflow-auto pb-4">
            {board.columns.map((column) => {
              const filteredCardIds = getFilteredCardIds(column.cardIds);
              return (
                <div key={column.id} className="w-[280px] shrink-0 lg:w-auto lg:flex-1">
                  <KanbanColumn
                    column={{ ...column, cardIds: filteredCardIds }}
                    cards={filteredCardIds.map((cardId) => board.cards[cardId])}
                    onRename={handleRenameColumn}
                    onAddCard={(colId) => setModal({ mode: "create", columnId: colId })}
                    onEditCard={(cardId) => setModal({ mode: "edit", cardId })}
                    onDeleteCard={handleDeleteCard}
                    onDeleteColumn={handleDeleteColumn}
                  />
                </div>
              );
            })}
            <button
              type="button"
              onClick={handleAddColumn}
              className="flex h-12 w-[280px] shrink-0 items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-[var(--stroke)] text-xs font-semibold text-[var(--primary-blue)] transition hover:border-[var(--primary-blue)] hover:bg-[var(--primary-blue)]/5 lg:w-48"
              aria-label="Add column"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5">
                <path d="M8.75 3.75a.75.75 0 0 0-1.5 0v3.5h-3.5a.75.75 0 0 0 0 1.5h3.5v3.5a.75.75 0 0 0 1.5 0v-3.5h3.5a.75.75 0 0 0 0-1.5h-3.5v-3.5Z" />
              </svg>
              Add column
            </button>
          </section>
          <DragOverlay>
            {activeCard ? (
              <div className="w-[240px]">
                <KanbanCardPreview card={activeCard} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>

      </div>

      {/* Floating chat window - outside layout flow */}
      {chatOpen && (
        <ChatPanel
          onClose={() => setChatOpen(false)}
          onBoardUpdated={loadBoard}
          boardId={boardId}
        />
      )}

      {modal?.mode === "create" && (
        <CardModal
          mode="create"
          columnName={board.columns.find((c) => c.id === modal.columnId)?.title}
          onSubmit={(title, details, dueDate) => {
            handleAddCard(modal.columnId, title, details, dueDate);
            setModal(null);
          }}
          onClose={() => setModal(null)}
        />
      )}

      {modal?.mode === "edit" && (
        <CardModal
          mode="edit"
          initialTitle={board.cards[modal.cardId]?.title}
          initialDetails={board.cards[modal.cardId]?.details}
          initialDueDate={board.cards[modal.cardId]?.due_date}
          initialLabels={board.cards[modal.cardId]?.labels}
          onSubmit={(title, details, dueDate, labels) => {
            handleEditCard(modal.cardId, title, details, dueDate, labels);
            setModal(null);
          }}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  );
};
