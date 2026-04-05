import { useCallback, useEffect, useRef, useState } from "react";
import { apiPost } from "../api";

type Role = "user" | "assistant";

interface ChatMessage {
  id: string;
  role: Role;
  content: string;
}

interface ChatResponse {
  status: string;
  agent_reply: string;
}

function uid(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function SysAdminChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: uid(),
      role: "assistant",
      content:
        "I'm the Conversational SysAdmin. Ask in plain language — system health, Docker list/restart/stop/start, inventory, and more (Ollama required for intent parsing).",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const listEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || busy) return;

    setMessages((m) => [...m, { id: uid(), role: "user", content: trimmed }]);
    setInput("");
    setBusy(true);

    try {
      const data = await apiPost<ChatResponse>("/api/chat", { message: trimmed });
      const reply = data.agent_reply ?? "No reply from orchestrator.";
      setMessages((m) => [...m, { id: uid(), role: "assistant", content: reply }]);
    } catch (e) {
      const err = e instanceof Error ? e.message : "Request failed.";
      setMessages((m) => [
        ...m,
        {
          id: uid(),
          role: "assistant",
          content: `Request failed: ${err}`,
        },
      ]);
    } finally {
      setBusy(false);
    }
  }, [input, busy]);

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
  };

  return (
    <div className="chat-shell">
      <div className="messages" aria-live="polite">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`bubble ${msg.role === "user" ? "user" : "assistant"}`}
          >
            <span className="bubble-label">
              {msg.role === "user" ? "You" : "SysAdmin"}
            </span>
            <p className="bubble-text">{msg.content}</p>
          </div>
        ))}
        {busy && (
          <div className="bubble assistant thinking">
            <span className="bubble-label">SysAdmin</span>
            <p className="bubble-text muted">Thinking…</p>
          </div>
        )}
        <div ref={listEndRef} />
      </div>

      <div className="composer">
        <textarea
          className="composer-input"
          rows={2}
          placeholder="Ask the orchestrator…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={busy}
          aria-label="Message"
        />
        <button
          type="button"
          className="composer-send"
          onClick={() => void sendMessage()}
          disabled={busy || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}
