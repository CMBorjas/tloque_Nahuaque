import { useCallback, useEffect, useRef, useState } from "react";
import "./App.css";

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

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

function uid(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: uid(),
      role: "assistant",
      content:
        "I'm the Conversational SysAdmin. Ask in plain language — for example: check system health, restart a container by name, or log inventory usage (with Ollama running for full intent parsing).",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const listEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const url = `${API_BASE}/health`;
    fetch(url)
      .then((r) => r.ok)
      .then(setBackendOk)
      .catch(() => setBackendOk(false));
  }, []);

  const sendMessage = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || busy) return;

    const userMsg: ChatMessage = { id: uid(), role: "user", content: trimmed };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setBusy(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed }),
      });

      if (!res.ok) {
        const detail = await res.text();
        throw new Error(detail || `HTTP ${res.status}`);
      }

      const data: ChatResponse = await res.json();
      const reply = data.agent_reply ?? "No reply from orchestrator.";

      setMessages((m) => [
        ...m,
        { id: uid(), role: "assistant", content: reply },
      ]);
      setBackendOk(true);
    } catch (e) {
      const err = e instanceof Error ? e.message : "Request failed.";
      setMessages((m) => [
        ...m,
        {
          id: uid(),
          role: "assistant",
          content: `Could not reach the orchestrator API. ${err}

Make sure the backend is running (\`python -m orchestrator.main\`) on port 8000, and that you're using \`npm run dev\` so Vite proxies \`/api\` — or set \`VITE_API_BASE\` to your API URL.`,
        },
      ]);
      setBackendOk(false);
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
    <div className="app">
      <header className="header">
        <div className="brand">
          <span className="brand-mark" aria-hidden />
          <div>
            <h1>Tloque Nahuaque</h1>
            <p className="tagline">Conversational SysAdmin</p>
          </div>
        </div>
        <div
          className={`status ${backendOk === true ? "ok" : backendOk === false ? "bad" : "unk"}`}
          title="Orchestrator /health"
        >
          {backendOk === true
            ? "Orchestrator online"
            : backendOk === false
              ? "API unreachable"
              : "Checking…"}
        </div>
      </header>

      <main className="chat-shell">
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
      </main>
    </div>
  );
}
