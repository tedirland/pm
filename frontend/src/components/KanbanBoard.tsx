"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
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
import { ChatSidebar } from "@/components/ChatSidebar";
import { moveCard, type BoardData } from "@/lib/kanban";
import {
  fetchBoard,
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
  onLogout?: () => void;
};

export const KanbanBoard = ({ username, onLogout }: KanbanBoardProps) => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [modal, setModal] = useState<ModalState>(null);
  const [chatOpen, setChatOpen] = useState(false);

  const loadBoard = useCallback(async () => {
    try {
      const data = await fetchBoard();
      setBoard(data);
      setError(null);
    } catch {
      setError("Failed to load board");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBoard();
  }, [loadBoard]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id || !board) return;

    const newColumns = moveCard(board.columns, active.id as string, over.id as string);
    setBoard((prev) => prev ? { ...prev, columns: newColumns } : prev);

    // Find where the card ended up
    const cardId = active.id as string;
    for (const col of newColumns) {
      const idx = col.cardIds.indexOf(cardId);
      if (idx !== -1) {
        moveCardApi(cardId, col.id, idx).catch(() => loadBoard());
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
    renameColumnApi(columnId, title).catch(() => loadBoard());
  };

  const handleAddCard = async (columnId: string, title: string, details: string) => {
    try {
      const card = await createCardApi(columnId, title, details);
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

  const handleEditCard = async (cardId: string, title: string, details: string) => {
    setBoard((prev) =>
      prev
        ? {
            ...prev,
            cards: {
              ...prev.cards,
              [cardId]: { ...prev.cards[cardId], title, details },
            },
          }
        : prev
    );
    try {
      await updateCardApi(cardId, title, details);
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
      await deleteCardApi(cardId);
    } catch {
      loadBoard();
    }
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
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-6 px-6 pb-16 pt-6">
        <header className="flex items-center justify-between rounded-2xl border border-[var(--stroke)] bg-white/80 px-6 py-3 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex items-center gap-3">
            <span className="h-2.5 w-2.5 rounded-full bg-[var(--accent-yellow)]" />
            <h1 className="font-display text-xl font-semibold text-[var(--navy-dark)]">
              Kanban Studio
            </h1>
          </div>
          {username && onLogout && (
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold text-[var(--gray-text)]">
                {username}
              </span>
              <button
                type="button"
                onClick={() => setChatOpen(true)}
                className="rounded-full border border-[var(--secondary-purple)] px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-[var(--secondary-purple)] transition hover:bg-[var(--secondary-purple)] hover:text-white"
              >
                AI Chat
              </button>
              <button
                type="button"
                onClick={onLogout}
                className="rounded-full border border-[var(--stroke)] px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
              >
                Sign out
              </button>
            </div>
          )}
        </header>

        <div className="flex items-center gap-3 overflow-x-auto">
          {board.columns.map((column) => {
            const count = column.cardIds.length;
            return (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] bg-white/80 px-3 py-1.5 text-xs font-semibold backdrop-blur"
              >
                <span className="text-[var(--navy-dark)]">{column.title}</span>
                <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--navy-dark)] px-1.5 text-[10px] font-bold text-white">
                  {count}
                </span>
              </div>
            );
          })}
          <div className="ml-auto flex items-center gap-2 text-xs font-semibold text-[var(--gray-text)]">
            <span>{Object.keys(board.cards).length} total</span>
          </div>
        </div>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <section className="grid items-start gap-6 lg:grid-cols-5">
            {board.columns.map((column) => (
              <KanbanColumn
                key={column.id}
                column={column}
                cards={column.cardIds.map((cardId) => board.cards[cardId])}
                onRename={handleRenameColumn}
                onAddCard={(colId) => setModal({ mode: "create", columnId: colId })}
                onEditCard={(cardId) => setModal({ mode: "edit", cardId })}
                onDeleteCard={handleDeleteCard}
              />
            ))}
          </section>
          <DragOverlay>
            {activeCard ? (
              <div className="w-[260px]">
                <KanbanCardPreview card={activeCard} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </main>

      {modal?.mode === "create" && (
        <CardModal
          mode="create"
          columnName={board.columns.find((c) => c.id === modal.columnId)?.title}
          onSubmit={(title, details) => {
            handleAddCard(modal.columnId, title, details);
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
          onSubmit={(title, details) => {
            handleEditCard(modal.cardId, title, details);
            setModal(null);
          }}
          onClose={() => setModal(null)}
        />
      )}

      <ChatSidebar
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        onBoardUpdated={loadBoard}
      />
    </div>
  );
};
