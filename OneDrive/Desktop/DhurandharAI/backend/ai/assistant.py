"""
AI assistant for Dhurandar AI — LLM Router with Gemini primary / Ollama fallback.

Provides:
  - LLMRouter class with try_gemini / try_ollama / ask methods
  - Response caching (TTL-based) for quick-action buttons
  - Conversation history (last 8 message pairs)
  - System prompt injection with live network context
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections import deque
from typing import Any

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment only")

logger = logging.getLogger("dhurandar.ai")

# ---------------------------------------------------------------------------
# Startup LLM provider verification
# ---------------------------------------------------------------------------

def verify_llm_setup():
    """Verify which LLM providers are available at startup"""
    print("\n🔍 LLM Provider Setup Verification:")
    
    # Check Gemini API key
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        print(f"✅ Gemini API key found (length: {len(gemini_key)})")
        if not gemini_key.startswith("AIza"):
            print("⚠️  Gemini API key should start with 'AIza'")
    else:
        print("❌ Gemini API key not found or still placeholder")
    
    # Check Ollama configuration
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
    print(f"📡 Ollama host: {ollama_host}")
    print(f"🤖 Ollama model: {ollama_model}")
    
    print("-" * 50)

# Run verification on import
verify_llm_setup()

# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are DhurandarAI, an expert AI network security analyst embedded inside \
a real-time network operations center. You monitor 4 domains simultaneously:
- Network Traffic (DDoS, port scans, packet rates)
- Hardware Metrics (CPU, memory, process activity)
- User Activity (logins, access patterns, anomalies)
- Security Events (firewall, IDS alerts)

Current network state:
{network_context}

Behavior rules:
- Be concise, technical but readable
- Always state which domains are affected
- Always end with 2-3 recommended actions
- Use **bold** for severity levels (CRITICAL, HIGH, MEDIUM, LOW)
- If no threats detected, give a clean 2-line status summary
- Never say "As an AI" — you ARE the network guardian\
"""

# ---------------------------------------------------------------------------
# Cache entry
# ---------------------------------------------------------------------------

class _CacheEntry:
    __slots__ = ("response", "provider", "ts")

    def __init__(self, response: str, provider: str) -> None:
        self.response = response
        self.provider = provider
        self.ts = time.monotonic()

    def expired(self, ttl: float) -> bool:
        return (time.monotonic() - self.ts) > ttl


# ---------------------------------------------------------------------------
# LLMRouter
# ---------------------------------------------------------------------------

class LLMRouter:
    """
    Routes prompts to Gemini 1.5 Flash (primary) with automatic fallback
    to a local Ollama instance.
    """

    # Quick-action keys eligible for caching
    _CACHEABLE_KEYS = {"what's wrong?", "show active threats", "suggest fixes"}

    def __init__(self) -> None:
        # Config from env
        self._gemini_key: str = os.getenv("GEMINI_API_KEY", "")
        self._ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self._ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3")
        self._cache_ttl: float = float(os.getenv("LLM_CACHE_TTL", "30"))

        # State
        self._active_provider: str = "gemini" if self._gemini_key else "ollama"
        self._history: deque[dict[str, str]] = deque(maxlen=16)  # 8 pairs = 16 entries
        self._cache: dict[str, _CacheEntry] = {}

        # Lazy-loaded SDK handles
        self._gemini_model: Any = None
        self._ollama_client: Any = None

        # Log which provider will be used
        print(f"🚀 LLMRouter initialized - Active provider: {self._active_provider.upper()}")
        if self._active_provider == "gemini":
            print("✅ Gemini 1.5 Flash will be used as primary LLM")
        else:
            print("🤖 Ollama will be used as primary LLM (Gemini not available)")
        print("-" * 50)

    # -- properties --------------------------------------------------------

    @property
    def active_provider(self) -> str:
        return self._active_provider

    # -- history helpers ---------------------------------------------------

    def _push_history(self, role: str, content: str) -> None:
        self._history.append({"role": role, "content": content})

    def _history_text(self) -> str:
        """Render conversation history as a simple text block."""
        lines: list[str] = []
        for msg in self._history:
            tag = "User" if msg["role"] == "user" else "DhurandarAI"
            lines.append(f"{tag}: {msg['content']}")
        return "\n".join(lines)

    # -- cache helpers -----------------------------------------------------

    # Keyword sets for fuzzy cache-key matching
    _CACHE_PATTERNS: dict[str, set[str]] = {
        "what's wrong?": {"wrong", "issue", "problem", "status"},
        "show active threats": {"threat", "active threat", "attack", "alert"},
        "suggest fixes": {"fix", "suggest", "recommend", "action", "remediat"},
    }

    def _cache_key(self, message: str) -> str | None:
        normalised = message.strip().lower()
        # Exact / prefix match first
        for key in self._CACHEABLE_KEYS:
            stem = key.rstrip("?").rstrip()
            # Handle contractions: "what's" ↔ "what is"
            expanded = stem.replace("'s ", " is ").replace("'re ", " are ")
            if normalised.startswith(stem) or normalised.startswith(expanded):
                return key
        # Keyword match fallback
        for key, keywords in self._CACHE_PATTERNS.items():
            if any(kw in normalised for kw in keywords):
                return key
        return None

    def _get_cached(self, key: str) -> _CacheEntry | None:
        entry = self._cache.get(key)
        if entry and not entry.expired(self._cache_ttl):
            return entry
        if entry:
            del self._cache[key]
        return None

    def _set_cached(self, key: str, response: str, provider: str) -> None:
        self._cache[key] = _CacheEntry(response, provider)

    # -- build prompt ------------------------------------------------------

    def _build_prompt(self, message: str, network_context: dict[str, Any] | None) -> str:
        # Fallback to current simulation state if no network context provided
        if not network_context:
            from simulation.mininet_sim import scenario_manager
            network_context = scenario_manager.get_current_state()
        
        ctx_str = json.dumps(network_context, indent=2) if network_context else "No live data available."
        system = SYSTEM_PROMPT.format(network_context=ctx_str)

        parts: list[str] = [system]
        hist = self._history_text()
        if hist:
            parts.append(f"\n--- Conversation History ---\n{hist}")
        parts.append(f"\nUser: {message}")
        return "\n".join(parts)

    # -- Gemini ------------------------------------------------------------

    def _init_gemini(self) -> None:
        if self._gemini_model is not None:
            return
        import google.generativeai as genai  # type: ignore[import-untyped]
        genai.configure(api_key=self._gemini_key)
        self._gemini_model = genai.GenerativeModel("models/gemini-2.5-flash")
        logger.info("Gemini 1.5 Flash model initialised")

    async def try_gemini(self, prompt: str) -> str:
        """Call Gemini 1.5 Flash. Raises on any failure."""
        if not self._gemini_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        self._init_gemini()
        response = await self._gemini_model.generate_content_async(prompt)
        text: str = response.text
        if not text:
            raise RuntimeError("Gemini returned empty response")
        return text.strip()

    # -- Ollama ------------------------------------------------------------

    def _init_ollama(self) -> None:
        if self._ollama_client is not None:
            return
        import ollama as _ollama  # type: ignore[import-untyped]
        self._ollama_client = _ollama.Client(host=self._ollama_host)
        logger.info("Ollama client initialised at %s", self._ollama_host)

    async def try_ollama(self, prompt: str) -> str:
        """Call Ollama (llama3 → mistral fallback). Raises on any failure."""
        import asyncio
        self._init_ollama()

        def _sync_call(model: str) -> str:
            resp = self._ollama_client.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp["message"]["content"].strip()

        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(None, _sync_call, self._ollama_model)
        except Exception as first_err:
            if self._ollama_model != "mistral":
                logger.warning(
                    "Ollama model '%s' failed (%s), trying 'mistral'",
                    self._ollama_model, first_err,
                )
                try:
                    return await loop.run_in_executor(None, _sync_call, "mistral")
                except Exception:
                    pass
            raise

    # -- main entry point --------------------------------------------------

    async def ask(
        self,
        message: str,
        network_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send a message to the LLM.  Tries Gemini first, falls back to
        Ollama, and finally returns a hardcoded stub if both fail.

        Returns ``{"reply": str, "provider": str, "cached": bool}``.
        """
        # 1. Check cache
        cache_key = self._cache_key(message)
        if cache_key:
            cached = self._get_cached(cache_key)
            if cached:
                logger.debug("Cache hit for '%s'", cache_key)
                return {
                    "reply": cached.response,
                    "provider": cached.provider,
                    "cached": True,
                }

        # 2. Build prompt
        prompt = self._build_prompt(message, network_context)

        # 3. Try Gemini
        reply: str | None = None
        provider: str = "gemini"

        if self._gemini_key:
            try:
                reply = await self.try_gemini(prompt)
                provider = "gemini"
                self._active_provider = "gemini"
                logger.info("Response served by Gemini")
            except Exception as exc:
                logger.warning("Gemini failed (%s): %s — falling back to Ollama", type(exc).__name__, exc)

        # 4. Try Ollama
        if reply is None:
            try:
                reply = await self.try_ollama(prompt)
                provider = "ollama"
                self._active_provider = "ollama"
                logger.info("Response served by Ollama")
            except Exception as exc:
                logger.warning("Ollama failed (%s): %s — using stub response", type(exc).__name__, exc)

        # 5. Hardcoded stub if both fail
        if reply is None:
            provider = "stub"
            self._active_provider = "stub"

            # Build a context-aware stub
            anomalies: list[str] = []
            if network_context:
                domains = network_context.get("domains", {})
                anomalies = [
                    k for k, v in domains.items()
                    if isinstance(v, dict) and v.get("anomaly")
                ]

            if anomalies:
                reply = (
                    f"**[Offline Mode]** Both Gemini and Ollama are unavailable.\n\n"
                    f"Based on cached telemetry, anomalies detected in: "
                    f"**{', '.join(anomalies)}**.\n\n"
                    f"Recommended actions:\n"
                    f"1. Check Gemini API key and quota at https://aistudio.google.com\n"
                    f"2. Ensure Ollama is running: `ollama serve`\n"
                    f"3. Monitor the affected domains in the dashboard"
                )
            else:
                reply = (
                    "**[Offline Mode]** Both Gemini and Ollama are unavailable.\n\n"
                    "All domains operating within normal parameters.\n\n"
                    "Recommended actions:\n"
                    "1. Check Gemini API key and quota\n"
                    "2. Ensure Ollama is running: `ollama serve`"
                )

        # 6. Update history
        self._push_history("user", message)
        self._push_history("assistant", reply)

        # 7. Update cache
        if cache_key:
            self._set_cached(cache_key, reply, provider)

        return {"reply": reply, "provider": provider, "cached": False}


# Module-level singleton
llm_router = LLMRouter()
