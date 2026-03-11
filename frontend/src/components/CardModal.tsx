"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { LabelPicker, LABEL_COLORS } from "@/components/LabelPicker";

type CardModalProps = {
  mode: "create" | "edit";
  columnName?: string;
  initialTitle?: string;
  initialDetails?: string;
  initialDueDate?: string | null;
  initialLabels?: string;
  onSubmit: (title: string, details: string, dueDate: string | null, labels: string | undefined) => void;
  onClose: () => void;
};

export const CardModal = ({
  mode,
  columnName,
  initialTitle = "",
  initialDetails = "",
  initialDueDate = null,
  initialLabels = "",
  onSubmit,
  onClose,
}: CardModalProps) => {
  const [title, setTitle] = useState(initialTitle);
  const [details, setDetails] = useState(initialDetails);
  const [dueDate, setDueDate] = useState(initialDueDate || "");
  const [labels, setLabels] = useState(initialLabels || "");
  const overlayRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!title.trim()) return;
    onSubmit(title.trim(), details.trim(), dueDate || null, labels || undefined);
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) onClose();
  };

  return (
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-50 flex items-center justify-center bg-[var(--navy-dark)]/40 backdrop-blur-sm"
    >
      <div className="w-full max-w-md rounded-3xl border border-[var(--stroke)] bg-white p-6 shadow-[var(--shadow)]">
        <h2 className="font-display text-lg font-semibold text-[var(--navy-dark)]">
          {mode === "create" ? "New card" : "Edit card"}
        </h2>
        {mode === "create" && columnName && (
          <p className="mt-1 text-xs font-semibold text-[var(--gray-text)]">
            Adding to <span className="text-[var(--primary-blue)]">{columnName}</span>
          </p>
        )}
        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label
              htmlFor="card-title"
              className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
            >
              Title
            </label>
            <input
              id="card-title"
              ref={titleRef}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Card title"
              className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm font-medium text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
              required
            />
          </div>
          <div>
            <label
              htmlFor="card-details"
              className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
            >
              Details
            </label>
            <textarea
              id="card-details"
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              placeholder="Add details..."
              rows={3}
              className="mt-1 w-full resize-none rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--gray-text)] outline-none transition focus:border-[var(--primary-blue)]"
            />
          </div>
          <div>
            <label
              htmlFor="card-due-date"
              className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
            >
              Due Date
            </label>
            <input
              id="card-due-date"
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="mt-1 w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
            />
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
              Labels
            </label>
            <LabelPicker value={labels} onChange={setLabels} />
          </div>
          <div className="flex items-center gap-2 pt-1">
            <button
              type="submit"
              className="rounded-full bg-[var(--secondary-purple)] px-5 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
            >
              {mode === "create" ? "Add card" : "Save"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export { LABEL_COLORS };
