"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { sendChat, type ChatMessage } from "@/lib/api";

type ChatSidebarProps = {
  open: boolean;
  onClose: () => void;
  onBoardUpdated: () => void;
};

export const ChatSidebar = ({ open, onClose, onBoardUpdated }: ChatSidebarProps) => {
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    const updatedHistory = [...history, userMsg];
    setHistory(updatedHistory);
    setInput("");
    setSending(true);

    try {
      const resp = await sendChat(text, history);
      const assistantMsg: ChatMessage = { role: "assistant", content: resp.message };
      setHistory([...updatedHistory, assistantMsg]);
      if (resp.board_updated) onBoardUpdated();
    } catch {
      const errorMsg: ChatMessage = {
        role: "assistant",
        content: "Sorry, something went wrong. Please try again.",
      };
      setHistory([...updatedHistory, errorMsg]);
    } finally {
      setSending(false);
    }
  }, [input, sending, history, onBoardUpdated]);

  return (
    <div
      className={`fixed right-0 top-0 z-50 flex h-full w-[360px] flex-col border-l border-[var(--stroke)] bg-white shadow-lg transition-transform duration-200 ${
        open ? "translate-x-0" : "translate-x-full"
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[var(--stroke)] px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-[var(--secondary-purple)]" />
          <h2 className="text-sm font-semibold text-[var(--navy-dark)]">AI Assistant</h2>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded p-1 text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
          aria-label="Close chat"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3" data-testid="chat-messages">
        {history.length === 0 && (
          <p className="text-center text-xs text-[var(--gray-text)]">
            Ask me to create, move, or edit cards on your board.
          </p>
        )}
        {history.map((msg, i) => (
          <div
            key={i}
            className={`mb-3 max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
              msg.role === "user"
                ? "ml-auto bg-[var(--navy-dark)] text-white"
                : "mr-auto bg-[var(--surface)] text-[var(--navy-dark)]"
            }`}
          >
            {msg.role === "user" ? msg.content : <FormattedMessage text={msg.content} />}
          </div>
        ))}
        {sending && (
          <div className="mr-auto mb-3 max-w-[85%] rounded-lg bg-[var(--surface)] px-3 py-2 text-sm text-[var(--gray-text)]">
            Thinking...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-[var(--stroke)] px-4 py-3">
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the AI..."
            disabled={sending}
            className="flex-1 rounded-lg border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)] disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="rounded-lg bg-[var(--secondary-purple)] px-3 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-40"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

/** Lightweight formatter: handles **bold**, bullet lists (- item), and line breaks. */
function FormattedMessage({ text }: { text: string }) {
  const lines = text.split("\n");
  const elements: ReactNode[] = [];
  let listItems: ReactNode[] = [];

  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}`} className="list-disc pl-4 my-1 space-y-0.5">
          {listItems}
        </ul>
      );
      listItems = [];
    }
  };

  lines.forEach((line, i) => {
    const trimmed = line.trim();
    if (trimmed.startsWith("- ")) {
      listItems.push(<li key={i}>{formatInline(trimmed.slice(2))}</li>);
    } else {
      flushList();
      if (trimmed === "") {
        elements.push(<br key={i} />);
      } else {
        elements.push(<p key={i} className="my-0.5">{formatInline(trimmed)}</p>);
      }
    }
  });
  flushList();

  return <>{elements}</>;
}

/** Replace **bold** and *italic* markers with styled spans. */
function formatInline(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const regex = /\*\*(.+?)\*\*|\*(.+?)\*/g;
  let last = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index));
    if (match[1]) {
      parts.push(<strong key={match.index}>{match[1]}</strong>);
    } else if (match[2]) {
      parts.push(<em key={match.index}>{match[2]}</em>);
    }
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}
