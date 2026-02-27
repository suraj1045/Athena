# 🏛️ THE SURAJ ENGINEERING MANIFESTO

This document defines the immutable coding standards for this repository. All AI agents must adhere to these principles to ensure "Enterprise-Grade" results that reflect a "Scientific Design" philosophy.

---

## 💎 1. THE ARCHITECTURAL CORE (SSoT)
- **Single Source of Truth:** Hardcoding is considered a technical debt violation. All configurations, feature toggles, and model parameters must reside in `src/config.py` using `pydantic-settings`.
- **Environment Isolation:** Secrets and local environment specifics must be strictly decoupled via `.env` files.
- **Atomic Modularity:** Logic must be decoupled into clean, testable units (Brain, Senses, Telephony, Orchestration). No "God Files."

## 🔬 2. SCIENTIFIC DESIGN & RESEARCH RIGOR
- **Performance First:** Prioritize O(n) efficiency. In AI/ML or CV contexts (YOLO, Tracking), optimize for low-latency execution and minimal memory footprint.
- **Privacy-Preserving Design:** When building surveillance or data-sensitive systems, implement "Privacy-by-Design." Minimize data retention and utilize cryptographic best practices where applicable.
- **Deterministic Outcomes:** Ensure logic is predictable. Use explicit state management and logging to provide a "Thought Trace" for every AI decision.

## 🏢 3. ENTERPRISE-GRADE PYTHON
- **Strict Typing:** Mandatory use of Python Type Hinting. No `Any` unless scientifically necessary.
- **Validation Layers:** Use Pydantic models for every data boundary (API requests, LLM outputs, DB records). 
- **Async-Native:** The foundation must be asynchronous (`async/await`) to handle high-concurrency and real-time streams (WebSockets/Telephony) without blocking.

## 🎙️ 4. CONVERSATIONAL VUI CONSTRAINTS
- **Clean Audio Pipeline:** Strictly forbid Markdown (`**`, `*`, `_`) in LLM outputs to prevent TTS artifacts. 
- **Barge-In Intelligence:** Implement 0.5s interruption sensitivity with a robust debounce mechanism.
- **Latency Optimization:** Keep response turns <30 words. Use sentence-level pseudo-streaming to begin playback immediately.
- **State Signals:** Use explicit system tokens like `[END_CALL]` for clean state transitions.

## 🛡️ 5. RESILIENCE & OBSERVABILITY
- **Graceful Degradation:** Always implement a fallback model (e.g., Haiku/Scout) for critical paths if the frontier model fails.
- **Telemetry:** Use structured JSON logging. Errors must trigger a detailed traceback in the console.
- **Layered Validation:** Maintain a `tests/` directory. No logic change is valid until it passes a Tier 1 (Logic) sandbox test.