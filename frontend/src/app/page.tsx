"use client";

import { useCallback, useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginForm } from "@/components/LoginForm";

type AuthState = "loading" | "logged-out" | "logged-in";

export default function Home() {
  const [auth, setAuth] = useState<AuthState>("loading");
  const [username, setUsername] = useState("");

  useEffect(() => {
    fetch("/api/me")
      .then((r) => {
        if (r.ok) return r.json();
        throw new Error("not authed");
      })
      .then((data) => {
        setUsername(data.username);
        setAuth("logged-in");
      })
      .catch(() => setAuth("logged-out"));
  }, []);

  const handleLogout = useCallback(async () => {
    await fetch("/api/logout", { method: "POST" });
    setAuth("logged-out");
    setUsername("");
  }, []);

  if (auth === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-[var(--gray-text)]">Loading...</p>
      </div>
    );
  }

  if (auth === "logged-out") {
    return (
      <LoginForm
        onLogin={(u) => {
          setUsername(u);
          setAuth("logged-in");
        }}
      />
    );
  }

  return <KanbanBoard username={username} onLogout={handleLogout} />;
}
