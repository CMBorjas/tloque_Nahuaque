import { useCallback, useEffect, useRef, useState } from "react";
import { apiPost } from "../api";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface ChatResponse {
  status: string;
  agent_reply: string;
}

function uid(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

const IDLE_MESSAGES = [
  "Need help? Click me!",
  "I can check your containers...",
  "Ask me anything!",
  "Try: 'show health'",
  "I'm your SysAdmin buddy!",
];

type Mood = "idle" | "happy" | "thinking" | "talking";

export function PetAssistant() {
  const [open, setOpen] = useState(false);
  const [mood, setMood] = useState<Mood>("idle");
  const [bubble, setBubble] = useState("Hi! I'm Nahua, your assistant!");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const listEndRef = useRef<HTMLDivElement>(null);
  const idleTimer = useRef<ReturnType<typeof setInterval>>();

  // idle animation cycle
  useEffect(() => {
    if (!open) {
      idleTimer.current = setInterval(() => {
        setBubble(IDLE_MESSAGES[Math.floor(Math.random() * IDLE_MESSAGES.length)]);
      }, 6000);
    }
    return () => clearInterval(idleTimer.current);
  }, [open]);

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || busy) return;

    setMessages((m) => [...m, { id: uid(), role: "user", content: trimmed }]);
    setInput("");
    setBusy(true);
    setMood("thinking");

    try {
      const data = await apiPost<ChatResponse>("/api/chat", { message: trimmed });
      const reply = data.agent_reply ?? "Hmm, no reply from the engine.";
      setMessages((m) => [...m, { id: uid(), role: "assistant", content: reply }]);
      setMood("happy");
      setTimeout(() => setMood("idle"), 3000);
    } catch (e) {
      const err = e instanceof Error ? e.message : "Request failed.";
      setMessages((m) => [
        ...m,
        { id: uid(), role: "assistant", content: `Oops: ${err}` },
      ]);
      setMood("idle");
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
    <div className="pet-wrapper">
      {/* Speech bubble when closed */}
      {!open && (
        <div className="pet-idle-bubble" onClick={() => setOpen(true)}>
          {bubble}
        </div>
      )}

      {/* Chat panel */}
      {open && (
        <div className="pet-chat-panel">
          <div className="pet-chat-header">
            <span className="pet-chat-title">Nahua</span>
            <button className="pet-chat-close" onClick={() => setOpen(false)}>
              &times;
            </button>
          </div>
          <div className="pet-chat-messages">
            {messages.length === 0 && (
              <p className="pet-chat-empty">
                Ask me anything! I can check containers, health, inventory...
              </p>
            )}
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`pet-msg ${msg.role === "user" ? "pet-msg-user" : "pet-msg-bot"}`}
              >
                {msg.content}
              </div>
            ))}
            {busy && (
              <div className="pet-msg pet-msg-bot pet-msg-thinking">
                <span className="pet-dots">
                  <span />
                  <span />
                  <span />
                </span>
              </div>
            )}
            <div ref={listEndRef} />
          </div>
          <div className="pet-chat-composer">
            <input
              className="pet-chat-input"
              placeholder="Ask Nahua..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              disabled={busy}
            />
            <button
              className="pet-chat-send"
              onClick={() => void sendMessage()}
              disabled={busy || !input.trim()}
            >
              Go
            </button>
          </div>
        </div>
      )}

      {/* The pet character */}
      <div
        className={`pet-character ${mood}`}
        onClick={() => setOpen((o) => !o)}
        title="Click to chat with Nahua!"
      >
        <div className="pet-body">
          <div className="pet-face">
            <div className="pet-eyes">
              <div className={`pet-eye left ${mood === "happy" ? "squint" : ""}`} />
              <div className={`pet-eye right ${mood === "happy" ? "squint" : ""}`} />
            </div>
            <div className={`pet-mouth ${mood}`} />
          </div>
          <div className="pet-antenna" />
        </div>
      </div>
    </div>
  );
}
