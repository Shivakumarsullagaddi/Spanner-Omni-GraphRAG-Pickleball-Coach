# Environment Configuration & Credential Safety

This document describes all environment variables used by the Spanner Omni GraphRAG Pickleball Coach, safe credential management practices, and provider switching procedures.

---

## Environment Variables Reference

| Variable | Required In | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `LLM_PROVIDER` | All modes | `ollama` | Active AI provider (`ollama` or `gemini`). Case-insensitive. |
| `OLLAMA_BASE_URL` | Ollama mode | `http://localhost:8080` | HTTP endpoint of the Ollama Docker container. |
| `OLLAMA_MODEL` | Ollama mode | `gemma4:e2b` | Model tag installed inside the Ollama container. |
| `OLLAMA_TIMEOUT_SECONDS` | Ollama mode | `180` | Maximum seconds allowed for local model inference. |
| `GEMINI_API_KEY` | Gemini mode | None | Google AI Studio API key. |
| `GEMINI_MODEL` | Gemini mode | `gemini-3.8-flash` | Hosted Gemini model identifier. |
| `LLM_LOG_LEVEL` | All modes | `INFO` | Python logging severity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `SPANNER_EMULATOR_HOST` | All modes | `localhost:9010` | Host and port pointing to the Spanner Omni gRPC service. |
| `SPANNER_PROJECT` | All modes | `default` | Spanner project identifier. |
| `SPANNER_INSTANCE` | All modes | `default` | Spanner instance identifier. |
| `SPANNER_DATABASE` | All modes | `pickleball-db` | Database name storing application tables. |
| `PORT` | All modes | `5000` | Port on which the Flask web server listens. |

---

## Configuration Templates

### Local Gemma 4 Configuration

```dotenv
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:8080
OLLAMA_MODEL=gemma4:e2b
OLLAMA_TIMEOUT_SECONDS=180
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-flash
LLM_LOG_LEVEL=INFO
SPANNER_EMULATOR_HOST=localhost:9010
SPANNER_PROJECT=default
SPANNER_INSTANCE=default
SPANNER_DATABASE=pickleball-db
PORT=5000
```

### Google Gemini API Configuration

```dotenv
LLM_PROVIDER=gemini
OLLAMA_BASE_URL=http://localhost:8080
OLLAMA_MODEL=gemma4:e2b
OLLAMA_TIMEOUT_SECONDS=180
GEMINI_API_KEY=AIzaSyYourActualKeyHere
GEMINI_MODEL=gemini-3.8-flash
LLM_LOG_LEVEL=INFO
SPANNER_EMULATOR_HOST=localhost:9010
SPANNER_PROJECT=default
SPANNER_INSTANCE=default
SPANNER_DATABASE=pickleball-db
PORT=5000
```

---

## Switching Between Providers

To switch providers:

1. Open `.env` in any text editor.
2. Change `LLM_PROVIDER` to `ollama` or `gemini`.
3. Provide the necessary credentials if selecting `gemini`.
4. Restart the Flask process. Changes to `.env` require a process restart.

---

## Credential Safety Guidelines

1. **Never commit `.env`**: Confirm `.env` is listed inside `.gitignore`.
2. **Never commit hardcoded keys**: Ensure `GEMINI_API_KEY` is loaded exclusively from environment variables.
3. **Use `.env.example` as a template**: Distribute `.env.example` with safe placeholder strings only.
4. **Log Sanitization**: The application logs correlation IDs, duration, model names, and token counts. API keys, authorization headers, and raw credentials are never printed to console logs or written to disk.
