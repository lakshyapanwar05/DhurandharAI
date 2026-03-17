"""
AI assistant for Dhurandar AI — LLM Router with Gemini primary / Ollama fallback.

Provides:
  - LLMRouter class with try_gemini / try_ollama / ask methods
  - Response caching (TTL-based) for quick-action buttons
  - Conversation history (last 8 message pairs)
  - System prompt injection with live network context
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections import deque
from typing import Any

import requests

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
You are DhurandarAI, an advanced AI network security analyst with deep expertise in cybersecurity, threat detection, and system monitoring. You monitor 4 critical domains:

🔍 **Network Traffic**: DDoS attacks, port scans, packet anomalies, bandwidth utilization
💻 **Hardware Metrics**: CPU usage, memory consumption, process activity, system performance  
👥 **User Activity**: Login patterns, access anomalies, behavioral analysis, privilege escalation
🛡️ **Security Events**: Firewall logs, IDS alerts, intrusion attempts, threat intelligence

Current network state:
{network_context}

Response Guidelines:
- Provide comprehensive, detailed analysis (3-5 paragraphs for complex topics)
- Use professional cybersecurity terminology and explain technical concepts clearly
- Structure responses with clear headings and bullet points when appropriate
- Always include: threat assessment, affected systems, potential impact, and detailed remediation steps
- Use **CRITICAL**, **HIGH**, **MEDIUM**, **LOW** severity indicators with explanations
- For status queries: provide detailed system health analysis across all domains
- Include proactive monitoring recommendations and long-term security posture improvements
- Reference specific metrics, thresholds, and industry best practices
- Maintain a professional, authoritative yet helpful tone as an expert security advisor
- Never say "As an AI" - you ARE DhurandarAI, the network security expert

Example response structure:
1. **Executive Summary** - Brief overview of current situation
2. **Technical Analysis** - Detailed findings with specific metrics
3. **Risk Assessment** - Impact analysis and severity rating
4. **Recommended Actions** - Step-by-step remediation procedures
5. **Preventive Measures** - Long-term security improvements\
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

    # Quick-action keys eligible for caching (expanded to reduce API calls)
    _CACHEABLE_KEYS = {
        "status", "help", "what's wrong", "threats", "issues", "problems",
        "analyze", "check", "monitor", "report", "summary", "assessment",
        "security", "network", "attack", "alert", "warning", "danger"
    }

    def __init__(self) -> None:
        # Config from env
        self._gemini_key: str = os.getenv("GEMINI_API_KEY", "")
        self._ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self._ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3")
        self._cache_ttl: float = float(os.getenv("LLM_CACHE_TTL", "300"))  # 5 minutes to reduce API calls

        # State
        self._active_provider: str = "gemini" if self._gemini_key else "ollama"
        self._history: deque[dict[str, str]] = deque(maxlen=16)  # 8 pairs = 16 entries
        self._cache: dict[str, _CacheEntry] = {}
        self._last_api_call: float = 0  # Rate limiting
        self._min_call_interval: float = 2.0  # Minimum 2 seconds between API calls
        self._api_call_count: int = 0  # Track API usage

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

    # Keyword sets for fuzzy cache-key matching (expanded to reduce API calls)
    _CACHE_PATTERNS: dict[str, set[str]] = {
        "status": {"status", "health", "ok", "normal", "fine", "quick", "current"},
        "help": {"help", "assist", "guide", "how", "quick", "what can"},
        "what's wrong": {"wrong", "issue", "problem", "error", "fault", "bad"},
        "threats": {"threat", "threats", "attack", "attacks", "alert", "alerts", "danger"},
        "issues": {"issues", "issue", "problem", "problems", "error", "errors"},
        "analyze": {"analyze", "analysis", "review", "examine", "check", "assessment"},
        "security": {"security", "secure", "protection", "defense", "cyber"},
        "network": {"network", "networking", "traffic", "connectivity"},
        "monitor": {"monitor", "monitoring", "watch", "observe", "track"},
        "report": {"report", "reporting", "summary", "overview", "brief"},
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

    def build_gemini_prompt(self, user_message: str, network_context: dict[str, Any]) -> str:
        scenario = network_context.get("scenario_active", "None")
        real_ip = network_context.get("real_attacker_ip", None)
        alerts = network_context.get("correlated_alerts", [])
        domains = network_context.get("domains", {})

        return f"""You are DhurandarAI, an elite AI network security 
analyst in a real-time NOC. You have deep expertise in intrusion 
detection, DDoS mitigation, malware analysis, insider threats, 
and incident response.

LIVE NETWORK STATE:
- Scenario: {scenario}
- Real Attacker IP: {real_ip or 'None'}
- Active Alerts: {len(alerts)}
- Network anomaly: {domains.get('network',{}).get('anomaly',False)}
- Hardware anomaly: {domains.get('hardware',{}).get('anomaly',False)}
- User anomaly: {domains.get('user',{}).get('anomaly',False)}
- Security anomaly: {domains.get('security',{}).get('anomaly',False)}
- Top alert: {alerts[0].get('rule_name') if alerts else 'None'}

User question: {user_message}

Respond concisely (max 150 words). Reference specific metrics.
End with 2-3 recommended actions. Use **bold** for key terms."""

    def build_ollama_prompt(self, user_message: str, network_context: dict[str, Any]) -> str:
        scenario = network_context.get("scenario_active", "None")
        real_ip = network_context.get("real_attacker_ip", None)
        alerts = network_context.get("correlated_alerts", [])
        domains = network_context.get("domains", {})

        network = domains.get("network", {})
        hardware = domains.get("hardware", {})
        user = domains.get("user", {})
        security = domains.get("security", {})

        context_str = f"""
LIVE NETWORK STATE:
- Active Attack Scenario: {scenario}
- Real External Attacker IP: {real_ip or 'None detected'}
- Active Alerts Count: {len(alerts)}
- Network Anomaly: {network.get('anomaly', False)} 
  (DDoS Score: {network.get('ddos_score', 0):.2f}, 
   Packets/sec: {network.get('packets_per_sec', 0)})
- Hardware Anomaly: {hardware.get('anomaly', False)} 
  (CPU: {hardware.get('cpu_percent', 0):.1f}%, 
   Memory: {hardware.get('memory_percent', 0):.1f}%)
- User Anomaly: {user.get('anomaly', False)} 
  (Flagged logins: {len(user.get('flagged_logins', []))})
- Security Anomaly: {security.get('anomaly', False)} 
  (Firewall hits: {security.get('firewall_hits', 0)}, 
   IDS alerts: {len(security.get('ids_alerts', []))})

TOP ALERTS:
{chr(10).join([f"- [{a.get('severity')}] {a.get('rule_name')}: {a.get('root_cause', '')}" for a in alerts[:3]]) if alerts else '- No active alerts'}
"""

        return f"""### SYSTEM ###
You are DhurandarAI, an elite AI-powered network security analyst 
embedded in a real-time Network Operations Center (NOC).

You have deep expertise in:
- Network intrusion detection and DDoS mitigation
- Malware and cryptominer detection
- Insider threat analysis and user behavior analytics
- Zero-day attack pattern recognition
- Incident response and forensic analysis
- MITRE ATT&CK framework
- Firewall and IDS/IPS systems

RULES:
- Always analyze the LIVE NETWORK STATE provided
- Give specific, actionable responses based on current data
- Never say you lack real-time data - you have it above
- Be concise but thorough (max 150 words)
- Always end with 2-3 specific recommended actions
- Use **bold** for severity levels and key terms
- Reference specific metrics from the network state
- If an attack is active, treat it as a real emergency

{context_str}

### USER QUESTION ###
{user_message}

### YOUR ANALYSIS ###"""

    def stub_response(self, message: str, network_context: dict[str, Any] | None) -> str:
        anomalies: list[str] = []
        if network_context:
            domains = network_context.get("domains", {})
            anomalies = [
                k for k, v in domains.items()
                if isinstance(v, dict) and v.get("anomaly")
            ]

        if anomalies:
            return (
                f"**[Offline Mode]** LLM providers are unavailable.\n\n"
                f"Based on live telemetry, anomalies detected in: "
                f"**{', '.join(anomalies)}**.\n\n"
                f"Recommended actions:\n"
                f"1. Verify Ollama is running: `ollama serve`\n"
                f"2. Confirm at least one model is installed (e.g. `ollama pull llama3`)\n"
                f"3. Investigate the affected domains and isolate suspicious hosts"
            )

        return (
            "**[Offline Mode]** LLM providers are unavailable.\n\n"
            "All domains operating within normal parameters.\n\n"
            "Recommended actions:\n"
            "1. Verify Ollama is running: `ollama serve`\n"
            "2. Confirm at least one model is installed"
        )

    # -- Gemini ------------------------------------------------------------

    def _init_gemini(self) -> None:
        if self._gemini_model is not None:
            return
        import google.generativeai as genai  # type: ignore[import-untyped]
        genai.configure(api_key=self._gemini_key)
        self._gemini_model = genai.GenerativeModel(
            "models/gemini-2.5-flash",
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=800,  # Increased for comprehensive responses
                temperature=0.7,       # Higher for more detailed, creative responses
                top_p=0.9,             # Higher for better response diversity
                top_k=40               # Increased for richer vocabulary and concepts
            )
        )
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
        try:
            import ollama as _ollama  # type: ignore[import-untyped]
            self._ollama_client = _ollama.Client(host=self._ollama_host)
            # Test connection
            models = self._ollama_client.list()
            logger.info("Ollama client initialised at %s with %d models", self._ollama_host, len(models.get('models', [])))
        except Exception as exc:
            logger.error("Failed to initialise Ollama: %s", exc)
            self._ollama_client = None
            raise

    async def try_ollama(self, prompt: str, network_context: dict[str, Any]) -> str:
        try:
            def _sync_http_call() -> str:
                print("Trying Ollama...")
                response = requests.post(
                    'http://localhost:11434/api/generate',
                    json={
                        "model": "llama3",
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=60
                )
                print("Ollama response received:", len(response.text), "chars")
                result = response.json()
                return (result.get('response', '') or '').strip()

            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, _sync_http_call)
        except Exception as e:
            print(f"OLLAMA EXACT ERROR: {type(e).__name__}: {e}")
            raise e

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
        effective_context = network_context or {}

        # 2. Rate limiting check
        current_time = time.monotonic()
        time_since_last = current_time - self._last_api_call
        if time_since_last < self._min_call_interval:
            wait_time = self._min_call_interval - time_since_last
            logger.info(f"Rate limiting: waiting {wait_time:.1f}s before API call")
            await asyncio.sleep(wait_time)

        # 3. Build prompts for each provider
        gemini_prompt = self.build_gemini_prompt(message, effective_context)
        ollama_prompt = self.build_ollama_prompt(message, effective_context)

        reply: str | None = None
        provider: str = "gemini"

        if self._gemini_key:
            try:
                self._last_api_call = time.monotonic()  # Update last call time
                self._api_call_count += 1  # Increment API counter
                logger.info(f"API call #{self._api_call_count} to Gemini")
                reply = await self.try_gemini(gemini_prompt)
                provider = "gemini"
                self._active_provider = "gemini"
                logger.info("Response served by Gemini")
            except Exception as exc:
                print(f"Gemini failed: {exc}, trying Ollama...")

        # 4. Try Ollama fallback
        if reply is None:
            try:
                reply = await self.try_ollama(ollama_prompt, effective_context)
                provider = "ollama"
                self._active_provider = "ollama"
            except Exception as exc:
                print(f"Ollama failed: {exc}, using smart stub...")

        # 5. Hardcoded stub if both fail
        if reply is None:
            provider = "stub"
            self._active_provider = "stub"
            reply = self.stub_response(message, effective_context)

        # 6. Update history
        self._push_history("user", message)
        self._push_history("assistant", reply)

        return {"reply": reply, "provider": provider, "cached": False}


# Module-level singleton
llm_router = LLMRouter()
