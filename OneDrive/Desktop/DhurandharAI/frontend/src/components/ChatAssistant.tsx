import { useState, useEffect, useRef, useCallback } from "react";
import anime from "animejs";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage, Domains, NetworkEvent } from "../types";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  networkContext: NetworkEvent | null;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const QUICK_ACTIONS = [
  { label: "What's wrong?", icon: "⚠" },
  { label: "Show active threats", icon: "🎯" },
  { label: "Suggest fixes", icon: "🔧" },
];

const GREETING: ChatMessage = {
  role: "assistant",
  content:
    "Hello. I'm monitoring your network across **4 domains** — Network Traffic, Hardware Metrics, User Activity, and Security Events.\n\nAsk me anything about your current threat landscape.",
  timestamp: new Date().toISOString(),
};

// ---------------------------------------------------------------------------
// Typing dots sub-component
// ---------------------------------------------------------------------------

function TypingDots() {
  const dotsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!dotsRef.current) return;
    const dots = dotsRef.current.querySelectorAll(".typing-dot");
    anime({
      targets: dots,
      translateY: [-4, 0],
      opacity: [0.3, 1],
      duration: 400,
      easing: "easeInOutSine",
      loop: true,
      direction: "alternate",
      delay: anime.stagger(120),
    });
    return () => {
      anime.remove(dots);
    };
  }, []);

  return (
    <div className="flex justify-start">
      <div className="bg-[#161b22] border border-[#00ff41]/10 rounded-2xl rounded-bl-md px-4 py-3">
        <div ref={dotsRef} className="flex items-center gap-1.5">
          <span className="typing-dot w-2 h-2 rounded-full bg-[#00ff41]" />
          <span className="typing-dot w-2 h-2 rounded-full bg-[#00ff41]" />
          <span className="typing-dot w-2 h-2 rounded-full bg-[#00ff41]" />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Markdown components for custom styling
// ---------------------------------------------------------------------------

const mdComponents = {
  p: ({ children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
    <p className="mb-2 last:mb-0 leading-relaxed" {...props}>
      {children}
    </p>
  ),
  strong: ({ children, ...props }: React.HTMLAttributes<HTMLElement>) => (
    <strong className="text-[#00ff41] font-semibold" {...props}>
      {children}
    </strong>
  ),
  ul: ({ children, ...props }: React.HTMLAttributes<HTMLUListElement>) => (
    <ul className="list-disc list-inside space-y-0.5 mb-2" {...props}>
      {children}
    </ul>
  ),
  ol: ({ children, ...props }: React.OlHTMLAttributes<HTMLOListElement>) => (
    <ol className="list-decimal list-inside space-y-0.5 mb-2" {...props}>
      {children}
    </ol>
  ),
  li: ({ children, ...props }: React.LiHTMLAttributes<HTMLLIElement>) => (
    <li className="text-white/70" {...props}>
      {children}
    </li>
  ),
  code: ({
    className,
    children,
    ...props
  }: React.HTMLAttributes<HTMLElement>) => {
    const isBlock = className?.includes("language-");
    if (isBlock) {
      return (
        <pre className="bg-black/40 border border-white/10 rounded-lg p-3 my-2 overflow-x-auto">
          <code
            className="text-[11px] font-mono text-[#00ff41]/80"
            {...props}
          >
            {children}
          </code>
        </pre>
      );
    }
    return (
      <code
        className="bg-white/10 text-[#00ff41] px-1 py-0.5 rounded text-[11px] font-mono"
        {...props}
      >
        {children}
      </code>
    );
  },
  h1: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h1 className="text-sm font-bold text-white/90 mb-1" {...props}>
      {children}
    </h1>
  ),
  h2: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h2 className="text-xs font-bold text-white/90 mb-1" {...props}>
      {children}
    </h2>
  ),
  h3: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h3 className="text-xs font-semibold text-white/80 mb-1" {...props}>
      {children}
    </h3>
  ),
  blockquote: ({
    children,
    ...props
  }: React.BlockquoteHTMLAttributes<HTMLQuoteElement>) => (
    <blockquote
      className="border-l-2 border-[#00ff41]/40 pl-3 my-2 text-white/50 italic"
      {...props}
    >
      {children}
    </blockquote>
  ),
};

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function ChatAssistant({ networkContext }: Props) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const panelRef = useRef<HTMLDivElement>(null);
  const btnRef = useRef<HTMLButtonElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const onlineDotRef = useRef<HTMLSpanElement>(null);

  // -----------------------------------------------------------------------
  // Animations
  // -----------------------------------------------------------------------

  // Floating button pulse
  useEffect(() => {
    if (!btnRef.current) return;
    anime({
      targets: btnRef.current,
      scale: [1, 1.06, 1],
      duration: 2600,
      easing: "easeInOutSine",
      loop: true,
    });
  }, []);

  // Online dot pulse in header
  useEffect(() => {
    if (!onlineDotRef.current || !open) return;
    const anim = anime({
      targets: onlineDotRef.current,
      scale: [1, 1.4, 1],
      opacity: [1, 0.5, 1],
      duration: 2000,
      easing: "easeInOutSine",
      loop: true,
    });
    return () => anim.pause();
  }, [open]);

  // Slide-up panel animation
  useEffect(() => {
    if (!panelRef.current || !open) return;
    anime({
      targets: panelRef.current,
      translateY: ["100%", "0%"],
      opacity: [0, 1],
      duration: 450,
      easing: "easeOutExpo",
    });
    // Focus input after opening
    setTimeout(() => inputRef.current?.focus(), 500);
  }, [open]);

  // Slide-down close animation
  const handleClose = useCallback(() => {
    if (!panelRef.current) {
      setOpen(false);
      return;
    }
    anime({
      targets: panelRef.current,
      translateY: ["0%", "100%"],
      opacity: [1, 0],
      duration: 300,
      easing: "easeInQuad",
      complete: () => setOpen(false),
    });
  }, []);

  // Auto-scroll on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Animate new message bubble
  const animateLastBubble = useCallback(() => {
    const container = bottomRef.current?.parentElement;
    if (!container) return;
    const bubbles = container.querySelectorAll(".chat-bubble");
    const last = bubbles[bubbles.length - 1];
    if (last) {
      anime({
        targets: last,
        translateY: [12, 0],
        opacity: [0, 1],
        duration: 350,
        easing: "easeOutExpo",
      });
    }
  }, []);

  // -----------------------------------------------------------------------
  // Send message
  // -----------------------------------------------------------------------

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || loading) return;

      const userMsg: ChatMessage = {
        role: "user",
        content: text.trim(),
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      setLoading(true);
      setTimeout(animateLastBubble, 30);

      try {
        console.log("[ChatAssistant] Sending message:", { message: text.trim(), network_context: networkContext });
        const res = await fetch("http://localhost:8000/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: text.trim(),
            network_context: networkContext, // Fixed: snake_case for backend
          }),
        });

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }

        const data = await res.json();
        console.log("[ChatAssistant] Response:", data);
        const aiMsg: ChatMessage = {
          role: "assistant",
          content: data.reply ?? "No response received.",
          provider: data.provider,
          cached: data.cached,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, aiMsg]);
        setTimeout(animateLastBubble, 30);
      } catch (error) {
        console.error("[ChatAssistant] API call failed:", error);
        const errMsg: ChatMessage = {
          role: "assistant",
          content: "**Connection Error** — Backend unreachable.\n\n**Error details:**\n- " + (error instanceof Error ? error.message : String(error)) + "\n\n**Recommended actions:**\n1. Verify backend is running on port 8000\n2. Check browser devtools console for CORS errors\n3. Ensure `python -m uvicorn app.main:app --reload` is running",
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errMsg]);
        setTimeout(animateLastBubble, 30);
      } finally {
        setLoading(false);
      }
    },
    [loading, networkContext, animateLastBubble]
  );

  // -----------------------------------------------------------------------
  // Keyboard shortcut: Escape to close
  // -----------------------------------------------------------------------
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && open) handleClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, handleClose]);

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  return (
    <>
      {/* -------- Floating trigger button -------- */}
      {!open && (
        <button
          ref={btnRef}
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-[#00ff41] text-black font-bold text-lg shadow-[0_0_30px_rgba(0,255,65,0.35)] hover:shadow-[0_0_45px_rgba(0,255,65,0.55)] transition-shadow flex items-center justify-center gap-0.5"
          title="Open AI Assistant"
        >
          <span className="text-base">AI</span>
        </button>
      )}

      {/* -------- Chat panel -------- */}
      {open && (
        <div
          ref={panelRef}
          className="fixed top-0 right-0 bottom-0 z-50 w-full sm:w-[35vw] sm:min-w-[380px] sm:max-w-[520px] flex flex-col border-l border-white/10 bg-[#0a0f0a]/[0.97] backdrop-blur-xl shadow-[-4px_0_40px_rgba(0,0,0,0.5)] opacity-0"
        >
          {/* ---- Header ---- */}
          <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/10 bg-[#0d1117]/80">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#00ff41]/15 border border-[#00ff41]/20 flex items-center justify-center">
                <span className="text-[#00ff41] text-sm font-bold">AI</span>
              </div>
              <div>
                <div className="text-sm font-semibold text-white/90 leading-tight">
                  DhurandarAI Assistant
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span
                    ref={onlineDotRef}
                    className="w-1.5 h-1.5 rounded-full bg-[#00ff41]"
                  />
                  <span className="text-[9px] text-[#00ff41]/70 font-mono uppercase">
                    Online
                  </span>
                </div>
              </div>
            </div>
            <button
              onClick={handleClose}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-white/30 hover:text-white/70 hover:bg-white/5 transition-all text-sm"
              title="Close (Esc)"
            >
              ✕
            </button>
          </div>

          {/* ---- Messages ---- */}
          <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 scrollbar-thin">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`chat-bubble flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {msg.role === "assistant" && (
                  <div className="w-6 h-6 rounded-md bg-[#00ff41]/10 border border-[#00ff41]/15 flex items-center justify-center shrink-0 mt-1 mr-2">
                    <span className="text-[10px] text-[#00ff41] font-bold">
                      AI
                    </span>
                  </div>
                )}
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-[13px] leading-relaxed ${
                    msg.role === "user"
                      ? "bg-[#00ff41]/12 text-[#b8ffca] border border-[#00ff41]/15 rounded-br-md"
                      : "bg-[#161b22] text-white/80 border border-[#00ff41]/10 rounded-bl-md"
                  }`}
                >
                  {msg.role === "assistant" ? (
                    <div className="markdown-body">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={mdComponents}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  )}
                  {/* Provider badge */}
                  {msg.provider && (
                    <div className="mt-1.5 flex items-center gap-2 text-[9px] text-white/20 font-mono">
                      <span className="uppercase px-1.5 py-0.5 rounded bg-white/5">
                        {msg.provider}
                      </span>
                      {msg.cached && (
                        <span className="px-1.5 py-0.5 rounded bg-[#00ff41]/10 text-[#00ff41]/50">
                          cached
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {loading && <TypingDots />}

            <div ref={bottomRef} />
          </div>

          {/* ---- Quick actions ---- */}
          <div className="px-5 py-2.5 flex gap-2 border-t border-white/5 bg-[#0d1117]/40">
            {QUICK_ACTIONS.map((q) => (
              <button
                key={q.label}
                onClick={() => sendMessage(q.label)}
                disabled={loading}
                className="flex items-center gap-1.5 shrink-0 text-[11px] font-mono px-3 py-1.5 rounded-full border border-[#00ff41]/15 text-[#00ff41]/60 hover:bg-[#00ff41]/10 hover:text-[#00ff41] hover:border-[#00ff41]/30 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <span className="text-xs">{q.icon}</span>
                {q.label}
              </button>
            ))}
          </div>

          {/* ---- Input ---- */}
          <div className="px-5 py-4 border-t border-white/10 bg-[#0d1117]/60">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                sendMessage(input);
              }}
              className="flex gap-2"
            >
              <input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about network security..."
                disabled={loading}
                className="flex-1 bg-[#161b22] border border-white/10 rounded-xl px-4 py-2.5 text-[13px] text-white/80 placeholder-white/20 outline-none focus:border-[#00ff41]/30 focus:shadow-[0_0_0_1px_rgba(0,255,65,0.1)] transition-all disabled:opacity-40"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="px-4 py-2.5 rounded-xl bg-[#00ff41]/15 text-[#00ff41] text-sm font-semibold hover:bg-[#00ff41]/25 border border-[#00ff41]/20 hover:border-[#00ff41]/40 transition-all disabled:opacity-20 disabled:cursor-not-allowed flex items-center gap-1.5"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M22 2L11 13" />
                  <path d="M22 2L15 22L11 13L2 9L22 2Z" />
                </svg>
                Send
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
