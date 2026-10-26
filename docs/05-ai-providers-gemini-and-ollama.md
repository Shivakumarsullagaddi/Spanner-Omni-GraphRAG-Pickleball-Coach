# AI Providers: Gemini API and Local Gemma 4 via Ollama

This document details the modular AI provider architecture supporting both hosted Google Gemini inference and local Gemma 4 inference through Ollama.

---

## 1. Provider Architecture

All AI generation calls in the application route through [`ai_service.py`](file:///D:/code_vipasana/pickleball/ai_service.py).
The service implements a common interface:

- `generate_text(prompt, system_instruction, feature_name)`
- `check_health()`

Both providers return a standardized `AIResponse` object containing generated text, provider identifier, model tag, request latency (in seconds), and token usage metrics.

---

## 2. Local Gemma 4 via Ollama

### Architecture
- **Container**: `gemma4-ollama-instance`
- **Image**: `gemma4-local`
- **Model**: `gemma4:e2b` (4.6 GB quantized local LLM)
- **Host Endpoint**: `http://localhost:8080`
- **API Endpoint**: `/api/chat` (non-streaming, JSON payload)

### Operation Details
1. **Thinking Tag Sanitization**: Gemma 4 thinking output (`<thought>...</thought>`) is automatically stripped before passing results to the application.
2. **Timeout Enforcement**: Configurable via `OLLAMA_TIMEOUT_SECONDS` (default: 180s) to prevent runaway processes during intensive CPU inference.
3. **No Fallback**: If Ollama is unreachable or times out, the application returns a clear error instead of silently falling back to a cloud service.

### Testing Ollama Directly

```powershell
$body = @{
    model = "gemma4:e2b"
    messages = @(
        @{ role = "user"; content = "Explain the kitchen rule in pickleball in 1 sentence." }
    )
    stream = $false
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8080/api/chat" -Method Post -Body $body -ContentType "application/json"
```

---

## 3. Google Gemini API

### Architecture
- **Model**: `gemini-3.8-flash`
- **SDK**: `google-genai` (with fallback to `google-generativeai`)
- **Authentication**: `GEMINI_API_KEY` loaded from environment

### Operation Details
1. Initialized only when `LLM_PROVIDER=gemini`.
2. Evaluates prompts combining system instructions, live Spanner database grounding, and user queries.
3. Does not invoke Ollama when selected.

---

## 4. Latency and Hardware Considerations

| Metric | Local Gemma 4 (`gemma4:e2b`) | Hosted Gemini 3.8 Flash |
| :--- | :--- | :--- |
| Execution Environment | Local CPU (Docker container) | Google Cloud Infrastructure |
| Network Dependency | 100% offline (no external calls) | Internet access required |
| Initial Model Load Time | ~40 to 50 seconds (first run after idle) | Immediate |
| Typical Inference Latency | ~45 to 90 seconds (prompt dependent) | ~1 to 3 seconds |
| Cost | Free (local hardware) | Standard API quota / pricing |

---

## 5. Structured Logging & Telemetry

Every inference event generates structured log output:

```text
[INFO] [pickleball.ai] [req_id] Started AI request: provider=ollama, model=gemma4:e2b, feature=concierge_chat, endpoint=http://localhost:8080
[INFO] [pickleball.ai] [req_id] Completed AI request: provider=ollama, model=gemma4:e2b, feature=concierge_chat, duration=51.74s, tokens=512, length=469
```

Logs never expose API keys, credentials, or full prompt histories.
