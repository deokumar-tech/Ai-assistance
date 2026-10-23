import { useEffect, useRef, useState, type FormEvent } from "react";
import { ArrowUp, AudioLines, Command, Mic, MicOff, ShieldCheck, Sparkles } from "lucide-react";
import InteractiveSynapseNetwork from "@/components/ui/interactive-synapse-network";

type Message = { id: number; role: "user" | "assistant"; text: string };
type RecognitionResultEvent = { results: ArrayLike<ArrayLike<{ transcript: string }>> };
type SpeechRecognitionLike = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: RecognitionResultEvent) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
};
type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;
type SpeechWindow = Window & {
  SpeechRecognition?: SpeechRecognitionConstructor;
  webkitSpeechRecognition?: SpeechRecognitionConstructor;
};

const suggestions = ["Open YouTube", "Check my battery", "Search for something"];

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [listening, setListening] = useState(false);
  const [status, setStatus] = useState<"online" | "offline">("online");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((response) => {
        if (!response.ok) throw new Error("API unavailable");
        setStatus("online");
      })
      .catch(() => setStatus("offline"));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    setDraft("");
    setMessages((current) => [...current, { id: Date.now(), role: "user", text: trimmed }]);
    setSending(true);
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: trimmed }),
      });
      const payload: { response?: string; detail?: string } = await response.json();
      if (!response.ok) throw new Error(payload.detail || "I couldn't reach the assistant.");
      setMessages((current) => [
        ...current,
        { id: Date.now() + 1, role: "assistant", text: payload.response ?? "I didn't get a response." },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: "assistant",
          text: error instanceof Error ? error.message : "Something went wrong. Please try again.",
        },
      ]);
      setStatus("offline");
    } finally {
      setSending(false);
    }
  }

  function toggleListening() {
    if (listening) {
      recognitionRef.current?.stop();
      return;
    }
    const speechWindow = window as SpeechWindow;
    const Recognition = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
    if (!Recognition) {
      setMessages((current) => [
        ...current,
        { id: Date.now(), role: "assistant", text: "Voice input isn't supported in this browser. You can type your request instead." },
      ]);
      return;
    }

    const recognition = new Recognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript;
      if (transcript) void sendMessage(transcript);
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => {
      setListening(false);
      recognitionRef.current = null;
    };
    recognitionRef.current = recognition;
    setListening(true);
    recognition.start();
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void sendMessage(draft);
  }

  return (
    <InteractiveSynapseNetwork
      ariaLabel="Igris interactive synapse network"
      nodeCount={56}
      connectionRadius={185}
      trailOpacity={0.18}
      className="igris-scene"
    >
      <main className="igris-shell">
        <header className="topbar">
          <a className="brand" href="#" aria-label="Igris home">
            <span className="brand-mark"><AudioLines size={20} strokeWidth={1.8} /></span>
            <span>IGRIS<span className="brand-period">.</span></span>
          </a>
          <div className="topbar-right">
            <span className={`status-pill ${status}`}>
              <span className="status-dot" />
              {status === "online" ? "SYSTEM ONLINE" : "API OFFLINE"}
            </span>
            <span className="topbar-divider" />
            <span className="local-badge"><ShieldCheck size={14} /> LOCAL API</span>
          </div>
        </header>

        <section className="assistant-panel" aria-label="Chat with Igris">
          <div className="conversation">
            {messages.length === 0 ? (
              <div className="welcome">
                <span className="eyebrow"><Sparkles size={14} /> YOUR PERSONAL ASSISTANT</span>
                <h1>At your command<span>.</span></h1>
                <p>What can I do for you?</p>
              </div>
            ) : (
              <div className="message-list" aria-live="polite">
                {messages.map((message) => (
                  <article className={`message ${message.role}`} key={message.id}>
                    {message.role === "assistant" && <span className="message-avatar"><AudioLines size={15} /></span>}
                    <p>{message.text}</p>
                  </article>
                ))}
                {sending && <div className="thinking"><span /><span /><span /> Igris is thinking</div>}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {messages.length === 0 && (
            <div className="suggestions" aria-label="Try asking">
              {suggestions.map((suggestion) => (
                <button key={suggestion} type="button" onClick={() => void sendMessage(suggestion)}>
                  {suggestion}
                </button>
              ))}
            </div>
          )}

          <form className="composer" onSubmit={handleSubmit}>
            <button
              className={`icon-button mic-button ${listening ? "listening" : ""}`}
              type="button"
              onClick={toggleListening}
              aria-label={listening ? "Stop voice input" : "Start voice input"}
              title={listening ? "Stop listening" : "Speak to Igris"}
            >
              {listening ? <MicOff size={19} /> : <Mic size={19} />}
            </button>
            <input
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder={listening ? "Listening..." : "Message Igris..."}
              aria-label="Message Igris"
              disabled={sending}
            />
            <span className="composer-hint"><Command size={12} /> ENTER</span>
            <button className="send-button" type="submit" disabled={!draft.trim() || sending} aria-label="Send message">
              <ArrowUp size={18} />
            </button>
          </form>
          <p className="privacy-note">Desktop actions run locally <span>·</span> AI requests use your configured provider</p>
        </section>

        <footer className="footer">
          <span>VOICE INTERFACE <i /></span>
          <span>BUILT FOR YOUR WORKFLOW</span>
          <span className="footer-hint">PRESS <kbd>F9</kbd> TO USE DESKTOP VOICE</span>
        </footer>
      </main>
    </InteractiveSynapseNetwork>
  );
}
