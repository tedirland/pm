"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { sendChat, type ChatMessage } from "@/lib/api";

type ChatPanelProps = {
  onBoardUpdated: () => void;
  boardId?: number;
  onClose: () => void;
};

export const ChatPanel = ({ onBoardUpdated, boardId, onClose }: ChatPanelProps) => {
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, sending]);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  const handleInputChange = (value: string) => {
    setInput(value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + "px";
    }
  };

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    const updatedHistory = [...history, userMsg];
    setHistory(updatedHistory);
    setInput("");
    setSending(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    try {
      const resp = await sendChat(text, history, boardId);
      const assistantMsg: ChatMessage = { role: "assistant", content: resp.message };
      setHistory([...updatedHistory, assistantMsg]);
      if (resp.board_updated) onBoardUpdated();
    } catch (err) {
      let errorContent = "Sorry, something went wrong. Please try again.";
      if (err instanceof Error) {
        if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
          errorContent = "Network error. Please check your connection and try again.";
        } else if (err.message.includes("401") || err.message.includes("authenticated")) {
          errorContent = "Session expired. Please refresh the page and sign in again.";
        }
      }
      setHistory([...updatedHistory, { role: "assistant", content: errorContent }]);
    } finally {
      setSending(false);
      textareaRef.current?.focus();
    }
  }, [input, sending, history, onBoardUpdated, boardId]);

  return (
    <>
      <style>{`
        @keyframes chat-enter {
          from { opacity: 0; transform: translateY(12px) scale(0.97); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes glow-pulse {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 0.8; }
        }
        @keyframes dot-fade {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 1; }
        }
        .chat-panel-enter {
          animation: chat-enter 0.25s cubic-bezier(0.16, 1, 0.3, 1) both;
        }
        .glow-thinking {
          animation: glow-pulse 2s ease-in-out infinite;
        }
        .dot-1 { animation: dot-fade 1.4s ease-in-out infinite; }
        .dot-2 { animation: dot-fade 1.4s ease-in-out 0.2s infinite; }
        .dot-3 { animation: dot-fade 1.4s ease-in-out 0.4s infinite; }
        .chat-scrollbar::-webkit-scrollbar { width: 4px; }
        .chat-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .chat-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 4px; }
        .chat-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.15); }
      `}</style>

      <div className="chat-panel-enter fixed bottom-5 right-5 z-50 flex h-[520px] w-[400px] flex-col overflow-hidden rounded-2xl border border-white/[0.08] shadow-[0_25px_60px_rgba(3,33,71,0.35),0_8px_20px_rgba(0,0,0,0.2)]"
        style={{ background: "linear-gradient(165deg, #0a1628 0%, #0d1f3c 40%, #111827 100%)" }}
      >
        <div
          className={`pointer-events-none absolute -top-20 left-1/2 h-40 w-60 -translate-x-1/2 rounded-full blur-3xl ${sending ? "glow-thinking" : "opacity-30"}`}
          style={{ background: "radial-gradient(circle, rgba(117,57,145,0.5) 0%, rgba(32,157,215,0.2) 60%, transparent 100%)" }}
        />

        <div className="relative z-10 flex items-center justify-between border-b border-white/[0.06] px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-gradient-to-br from-[#753991] to-[#209dd7]">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="white" className="h-4 w-4 opacity-90">
                  <path d="M10 1a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 1zM5.05 3.05a.75.75 0 011.06 0l1.062 1.06A.75.75 0 116.11 5.173L5.05 4.11a.75.75 0 010-1.06zm9.9 0a.75.75 0 010 1.06l-1.06 1.062a.75.75 0 01-1.062-1.061l1.061-1.06a.75.75 0 011.06 0zM10 7a3 3 0 100 6 3 3 0 000-6zm-6.25 3a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5H3a.75.75 0 01.75.75zm14 0a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5H17a.75.75 0 01.75.75z" />
                </svg>
              </div>
              <div className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-[#0d1f3c] bg-emerald-400" />
            </div>
            <div>
              <h2 className="text-[13px] font-semibold tracking-tight text-white/90">AI Assistant</h2>
              <p className="text-[10px] tracking-wide text-white/30">
                {sending ? "Thinking..." : "Can modify your board"}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-white/25 transition-all duration-200 hover:bg-white/[0.06] hover:text-white/60"
            aria-label="Close chat"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M3.5 3.5l7 7M10.5 3.5l-7 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        <div className="chat-scrollbar relative flex-1 overflow-y-auto" data-testid="chat-messages">
          <div className="px-4 py-4">
            {history.length === 0 && <EmptyState />}
            {history.map((msg, i) => (
              <MessageBubble key={i} message={msg} isConsecutive={i > 0 && history[i - 1].role === msg.role} />
            ))}
            {sending && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>
        </div>

        <div className="relative z-10 border-t border-white/[0.06] p-3">
          <div className="pointer-events-none absolute left-4 right-4 top-0 h-px bg-gradient-to-r from-transparent via-[#753991]/20 to-transparent" />

          <form
            className="flex items-end gap-2.5 rounded-xl border border-white/[0.06] bg-white/[0.03] px-3 py-2.5 transition-colors focus-within:border-white/[0.12] focus-within:bg-white/[0.05]"
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
          >
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => handleInputChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Message AI Assistant..."
              disabled={sending}
              rows={1}
              className="flex-1 resize-none bg-transparent text-[13px] leading-5 text-white/80 outline-none placeholder:text-white/20 disabled:opacity-40"
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="group mb-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-[#753991] to-[#209dd7] text-white transition-all duration-200 hover:shadow-[0_0_16px_rgba(117,57,145,0.4)] disabled:opacity-20 disabled:shadow-none"
              aria-label="Send"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3 w-3 transition-transform duration-200 group-hover:-translate-y-px group-hover:translate-x-px">
                <path d="M2.87 2.298a.75.75 0 00-.812.81l.81 4.057a.75.75 0 00.737.623h4.145a.5.5 0 010 1H3.605a.75.75 0 00-.737.624l-.81 4.056a.75.75 0 00.812.81l10.2-4.42a.75.75 0 000-1.378l-10.2-4.42z" />
              </svg>
            </button>
          </form>
          <p className="mt-2 text-center text-[10px] tracking-wide text-white/15">
            Enter to send · Shift+Enter for new line · Esc to close
          </p>
        </div>
      </div>
    </>
  );
};

function EmptyState() {
  return (
    <div className="flex flex-col items-center py-10">
      <div className="relative">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#753991]/20 to-[#209dd7]/20 ring-1 ring-white/[0.06]">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-6 w-6 text-[#209dd7]/70">
            <path d="M3.43 2.524A41.29 41.29 0 0110 2c2.236 0 4.43.18 6.57.524 1.437.231 2.43 1.49 2.43 2.902v5.148c0 1.413-.993 2.67-2.43 2.902a41.102 41.102 0 01-3.55.414c-.28.02-.521.18-.643.413l-1.712 3.293a.75.75 0 01-1.33 0l-1.713-3.293a.783.783 0 00-.642-.413 41.108 41.108 0 01-3.55-.414C1.993 13.245 1 11.986 1 10.574V5.426c0-1.413.993-2.67 2.43-2.902z" />
          </svg>
        </div>
        <div className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-[#ecad0a]/40" />
        <div className="absolute -bottom-1 -left-1.5 h-1.5 w-1.5 rounded-full bg-[#209dd7]/30" />
      </div>
      <h3 className="mt-4 text-sm font-semibold tracking-tight text-white/80">AI Assistant</h3>
      <p className="mt-1.5 max-w-[240px] text-center text-[12px] leading-relaxed text-white/30">
        I can create, move, edit, and delete cards on your board. Just ask.
      </p>
      <div className="mt-5 flex items-center gap-2">
        {["Create a card", "Organize tasks", "Set due dates"].map((hint) => (
          <span key={hint} className="rounded-full border border-white/[0.06] bg-white/[0.02] px-2.5 py-1 text-[10px] tracking-wide text-white/25">
            {hint}
          </span>
        ))}
      </div>
    </div>
  );
}

function MessageBubble({ message, isConsecutive }: { message: ChatMessage; isConsecutive: boolean }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-2.5 ${isConsecutive ? "mt-1" : "mt-5 first:mt-0"} ${isUser ? "flex-row-reverse" : ""}`}>
      {!isConsecutive && (
        <div className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-[8px] ${
          isUser
            ? "bg-[#209dd7]/15 ring-1 ring-[#209dd7]/20"
            : "bg-gradient-to-br from-[#753991]/20 to-[#209dd7]/20 ring-1 ring-white/[0.06]"
        }`}>
          {isUser ? (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3 w-3 text-[#209dd7]/70">
              <path d="M8 8a3 3 0 100-6 3 3 0 000 6zM12.735 14c.618 0 1.093-.561.872-1.139a6.002 6.002 0 00-11.215 0c-.22.578.255 1.139.872 1.139h9.47z" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3 w-3 text-[#209dd7]/60">
              <path d="M8 1a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 018 1zM4.11 2.611a.75.75 0 011.06 0l.849.848a.75.75 0 01-1.061 1.06l-.849-.848a.75.75 0 010-1.06zm7.78 0a.75.75 0 010 1.06l-.848.849a.75.75 0 01-1.061-1.06l.849-.849a.75.75 0 011.06 0zM8 5.5a2.5 2.5 0 100 5 2.5 2.5 0 000-5zM2.75 7.25a.75.75 0 000 1.5h1.5a.75.75 0 000-1.5h-1.5zm9 0a.75.75 0 000 1.5h1.5a.75.75 0 000-1.5h-1.5z" />
            </svg>
          )}
        </div>
      )}
      <div className={`flex min-w-0 max-w-[82%] flex-col ${isConsecutive ? (isUser ? "mr-[36px]" : "ml-[36px]") : ""}`}>
        {!isConsecutive && (
          <span className={`mb-1 text-[10px] font-medium tracking-wide ${isUser ? "text-right text-[#209dd7]/50" : "text-white/30"}`}>
            {isUser ? "You" : "AI Assistant"}
          </span>
        )}
        <div
          className={`rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed break-words overflow-hidden ${
            isUser
              ? "rounded-tr-md bg-[#209dd7]/15 text-white/80 ring-1 ring-[#209dd7]/10"
              : "rounded-tl-md bg-white/[0.04] text-white/65 ring-1 ring-white/[0.04]"
          }`}
        >
          {isUser ? message.content : <FormattedMessage text={message.content} />}
        </div>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="mt-5 flex gap-2.5">
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[8px] bg-gradient-to-br from-[#753991]/20 to-[#209dd7]/20 ring-1 ring-white/[0.06]">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="h-3 w-3 text-[#209dd7]/60">
          <path d="M8 1a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 018 1zM4.11 2.611a.75.75 0 011.06 0l.849.848a.75.75 0 01-1.061 1.06l-.849-.848a.75.75 0 010-1.06zm7.78 0a.75.75 0 010 1.06l-.848.849a.75.75 0 01-1.061-1.06l.849-.849a.75.75 0 011.06 0zM8 5.5a2.5 2.5 0 100 5 2.5 2.5 0 000-5zM2.75 7.25a.75.75 0 000 1.5h1.5a.75.75 0 000-1.5h-1.5zm9 0a.75.75 0 000 1.5h1.5a.75.75 0 000-1.5h-1.5z" />
        </svg>
      </div>
      <div className="flex flex-col">
        <span className="mb-1 text-[10px] font-medium tracking-wide text-white/30">AI Assistant</span>
        <div className="rounded-2xl rounded-tl-md bg-white/[0.04] px-4 py-3 ring-1 ring-white/[0.04]">
          <div className="flex items-center gap-1.5">
            <span className="dot-1 inline-block h-1.5 w-1.5 rounded-full bg-white/40" />
            <span className="dot-2 inline-block h-1.5 w-1.5 rounded-full bg-white/40" />
            <span className="dot-3 inline-block h-1.5 w-1.5 rounded-full bg-white/40" />
          </div>
        </div>
      </div>
    </div>
  );
}

function FormattedMessage({ text }: { text: string }) {
  const lines = text.split("\n");
  const elements: ReactNode[] = [];
  let listItems: ReactNode[] = [];

  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}`} className="list-disc pl-4 my-1.5 space-y-1 marker:text-white/20">
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

function formatInline(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const regex = /\*\*(.+?)\*\*|\*(.+?)\*/g;
  let last = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index));
    if (match[1]) {
      parts.push(<strong key={match.index} className="font-semibold text-white/90">{match[1]}</strong>);
    } else if (match[2]) {
      parts.push(<em key={match.index} className="italic text-white/40">{match[2]}</em>);
    }
    last = match.index + match[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}
