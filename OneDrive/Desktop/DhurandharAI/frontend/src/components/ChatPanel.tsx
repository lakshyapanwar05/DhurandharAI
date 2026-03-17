import { useState, useEffect, useRef } from "react";
import anime from "animejs";
import type { ChatMessage, Domains } from "../types";

interface Props {
  networkContext: { domains: Domains } | null;
}

const QUICK_ACTIONS = ["What's wrong?", "Show active threats", "Suggest fixes"];

export default function ChatPanel({ networkContext }: Props) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const btnRef = useRef<HTMLButtonElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Floating button pulse
  useEffect(() => {
    if (!btnRef.current) return;
    anime({
      targets: btnRef.current,
      scale: [1, 1.05, 1],
      duration: 2400,
      easing: "easeInOutSine",
      loop: true,
    });
  }, []);

  // Slide-up animation
  useEffect(() => {
    if (!panelRef.current) return;
    if (open) {
      anime({
        targets: panelRef.current,
        translateY: ["100%", "0%"],
        opacity: [0, 1],
        duration: 400,
        easing: "easeOutExpo",
      });
    }
  }, [open]);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;
    const userMsg: ChatMessage = {
      role: "user",
      content: text.trim(),
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text.trim(),
          networkContext: networkContext,
        }),
      });
      const data = await res.json();
      const aiMsg: ChatMessage = {
        role: "assistant",
        content: data.reply ?? "No response received.",
        provider: data.provider,
        cached: data.cached,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Connection error — backend unreachable.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating chat button */}
      {!open && (
        <button
          ref={btnRef}
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-[#00ff41] text-black font-bold text-xl shadow-[0_0_25px_rgba(0,255,65,0.3)] hover:shadow-[0_0_35px_rgba(0,255,65,0.5)] transition-shadow flex items-center justify-center"
        >
          AI
        </button>
      )}

      {/* Chat panel */}
      {open && (
        <div
          ref={panelRef}
          className="fixed bottom-0 right-0 z-50 w-full sm:w-[420px] h-[520px] flex flex-col rounded-tl-2xl rounded-tr-2xl sm:rounded-tr-none sm:right-6 sm:bottom-6 sm:rounded-2xl border border-white/10 bg-[#0a0f0a]/95 backdrop-blur-xl shadow-2xl opacity-0"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-[#00ff41]/20 flex items-center justify-center">
                <span className="text-[#00ff41] text-xs font-bold">AI</span>
              </div>
              <span className="text-sm font-semibold text-white/90">
                DhurandarAI Assistant
              </span>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-white/40 hover:text-white/80 transition-colors text-lg leading-none"
            >
              ✕
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 scrollbar-thin">
            {messages.length === 0 && (
              <div className="text-center py-8">
                <div className="text-2xl mb-2">🛡️</div>
                <div className="text-xs text-white/40">
                  Ask me about network threats, anomalies, or recommended
                  actions.
                </div>
              </div>
            )}
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed ${
                    msg.role === "user"
                      ? "bg-[#00ff41]/15 text-[#00ff41] border border-[#00ff41]/20"
                      : "bg-white/5 text-white/80 border border-white/5"
                  }`}
                >
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                  {msg.provider && (
                    <div className="mt-1 flex items-center gap-2 text-[9px] text-white/25">
                      <span className="uppercase">{msg.provider}</span>
                      {msg.cached && <span>• cached</span>}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white/5 border border-white/5 rounded-xl px-3 py-2 text-xs text-white/40">
                  <span className="animate-pulse">Analyzing...</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Quick actions */}
          <div className="px-4 py-2 flex gap-2 overflow-x-auto border-t border-white/5">
            {QUICK_ACTIONS.map((q) => (
              <button
                key={q}
                onClick={() => sendMessage(q)}
                disabled={loading}
                className="shrink-0 text-[10px] font-mono px-2.5 py-1 rounded-full border border-[#00ff41]/20 text-[#00ff41]/70 hover:bg-[#00ff41]/10 hover:text-[#00ff41] transition-colors disabled:opacity-40"
              >
                {q}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="px-4 py-3 border-t border-white/10">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                sendMessage(input);
              }}
              className="flex gap-2"
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about network security..."
                disabled={loading}
                className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/80 placeholder-white/25 outline-none focus:border-[#00ff41]/40 transition-colors disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="px-3 py-2 rounded-lg bg-[#00ff41]/15 text-[#00ff41] text-xs font-semibold hover:bg-[#00ff41]/25 transition-colors disabled:opacity-30"
              >
                Send
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
