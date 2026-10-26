import os
import re
import time
import uuid
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import requests

logger = logging.getLogger("pickleball.ai")


@dataclass
class AIResponse:
    text: str
    provider: str
    model: str
    duration_seconds: float
    token_usage: Optional[int] = None

    @property
    def source_label(self) -> str:
        if self.provider == "ollama":
            return f"Local Gemma 4 ({self.model})"
        return f"Gemini ({self.model})"


class BaseLLMProvider:
    def __init__(self, model: str):
        self.model = model

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        feature_name: str = "general",
    ) -> AIResponse:
        raise NotImplementedError

    def check_health(self) -> Dict[str, Any]:
        raise NotImplementedError


class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str, model: str, timeout_seconds: float = 180.0):
        super().__init__(model)
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

        parsed = urlparse(self.base_url)
        self.sanitized_host = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else self.base_url

        if not self.model:
            raise ValueError("OLLAMA_MODEL must not be empty when LLM_PROVIDER=ollama")

    def check_health(self) -> Dict[str, Any]:
        tags_url = f"{self.base_url}/api/tags"
        try:
            res = requests.get(tags_url, timeout=5)
            if res.status_code != 200:
                return {
                    "reachable": False,
                    "model_available": False,
                    "error": f"HTTP {res.status_code} from {self.sanitized_host}/api/tags",
                }
            data = res.json()
            models = data.get("models", [])
            model_names = [m.get("name") for m in models] + [m.get("model") for m in models]
            target = self.model
            base_target = target.split(":")[0]
            model_exists = any(
                target == m or m == f"{target}:latest" or (m and m.startswith(target))
                for m in model_names
                if m
            )
            return {
                "reachable": True,
                "model_available": model_exists,
                "error": None if model_exists else f"Model '{self.model}' not found in Ollama",
            }
        except requests.exceptions.Timeout:
            return {
                "reachable": False,
                "model_available": False,
                "error": f"Timeout connecting to Ollama at {self.sanitized_host}",
            }
        except requests.exceptions.ConnectionError:
            return {
                "reachable": False,
                "model_available": False,
                "error": f"Connection refused at {self.sanitized_host}",
            }
        except Exception as e:
            return {
                "reachable": False,
                "model_available": False,
                "error": str(e),
            }

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        feature_name: str = "general",
    ) -> AIResponse:
        req_id = uuid.uuid4().hex[:8]
        endpoint = f"{self.base_url}/api/chat"

        logger.info(
            "[%s] Started AI request: provider=ollama, model=%s, feature=%s, endpoint=%s",
            req_id,
            self.model,
            feature_name,
            self.sanitized_host,
        )

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": 512,
            },
        }

        start_time = time.perf_counter()
        try:
            res = requests.post(
                endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout_seconds,
            )
        except requests.exceptions.Timeout:
            duration = time.perf_counter() - start_time
            err_msg = f"Inference timed out after {self.timeout_seconds}s"
            logger.error(
                "[%s] AI request failed: provider=ollama, feature=%s, duration=%.2fs, error=%s",
                req_id,
                feature_name,
                duration,
                err_msg,
            )
            raise TimeoutError(f"Ollama request timed out after {self.timeout_seconds}s")
        except requests.exceptions.ConnectionError:
            duration = time.perf_counter() - start_time
            err_msg = f"Cannot reach Ollama server at {self.sanitized_host}"
            logger.error(
                "[%s] AI request failed: provider=ollama, feature=%s, duration=%.2fs, error=%s",
                req_id,
                feature_name,
                duration,
                err_msg,
            )
            raise ConnectionError(f"Cannot reach Ollama at {self.sanitized_host}")
        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(
                "[%s] AI request failed: provider=ollama, feature=%s, duration=%.2fs, error=%s",
                req_id,
                feature_name,
                duration,
                str(e),
            )
            raise RuntimeError(f"Ollama request error: {e}")

        duration = time.perf_counter() - start_time

        if res.status_code == 404:
            logger.error(
                "[%s] Ollama returned 404: model=%s not found",
                req_id,
                self.model,
            )
            raise ValueError(f"Ollama model '{self.model}' not found on server")

        if res.status_code != 200:
            logger.error(
                "[%s] Ollama returned HTTP %d: %s",
                req_id,
                res.status_code,
                res.text[:200],
            )
            raise RuntimeError(f"Ollama HTTP {res.status_code}: {res.text[:200]}")

        try:
            data = res.json()
        except Exception as e:
            logger.error("[%s] Malformed JSON response from Ollama: %s", req_id, str(e))
            raise ValueError("Malformed response from Ollama")

        message = data.get("message", {})
        raw_text = message.get("content", "")
        cleaned_text = re.sub(r"<thought>.*?</thought>", "", raw_text, flags=re.DOTALL).strip()
        tokens_used = data.get("eval_count")

        logger.info(
            "[%s] Completed AI request: provider=ollama, model=%s, feature=%s, duration=%.2fs, tokens=%s, length=%d",
            req_id,
            self.model,
            feature_name,
            duration,
            tokens_used,
            len(cleaned_text),
        )

        return AIResponse(
            text=cleaned_text,
            provider="ollama",
            model=self.model,
            duration_seconds=round(duration, 3),
            token_usage=tokens_used,
        )


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-3.8-flash"):
        super().__init__(model)
        self.api_key = api_key.strip() if api_key else ""
        if not self.api_key or self.api_key == "your_gemini_api_key_here" or self.api_key == "your-gemini-api-key":
            raise ValueError("A valid GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        if not self.model:
            raise ValueError("GEMINI_MODEL must not be empty when LLM_PROVIDER=gemini")

        self.client = None
        self._init_client()

    def _init_client(self):
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except Exception:
            try:
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=self.api_key)
                self.client = legacy_genai.GenerativeModel(self.model)
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Gemini SDK client: {e}")

    def check_health(self) -> Dict[str, Any]:
        return {
            "reachable": bool(self.client),
            "model_available": bool(self.client),
            "error": None,
        }

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        feature_name: str = "general",
    ) -> AIResponse:
        req_id = uuid.uuid4().hex[:8]

        logger.info(
            "[%s] Started AI request: provider=gemini, model=%s, feature=%s",
            req_id,
            self.model,
            feature_name,
        )

        if not self.client:
            raise RuntimeError("Gemini client is not initialized")

        combined_prompt = (
            f"{system_instruction}\n\nUser Question: {prompt}"
            if system_instruction
            else prompt
        )

        start_time = time.perf_counter()
        try:
            if hasattr(self.client, "models"):
                res = self.client.models.generate_content(
                    model=self.model,
                    contents=combined_prompt,
                )
                generated_text = res.text or ""
            elif hasattr(self.client, "generate_content"):
                res = self.client.generate_content(combined_prompt)
                generated_text = res.text or ""
            else:
                raise RuntimeError("Unsupported Gemini client object")
        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(
                "[%s] AI request failed: provider=gemini, feature=%s, duration=%.2fs, error=%s",
                req_id,
                feature_name,
                duration,
                str(e),
            )
            raise RuntimeError(f"Gemini API request failed: {e}")

        duration = time.perf_counter() - start_time

        logger.info(
            "[%s] Completed AI request: provider=gemini, model=%s, feature=%s, duration=%.2fs, length=%d",
            req_id,
            self.model,
            feature_name,
            duration,
            len(generated_text),
        )

        return AIResponse(
            text=generated_text,
            provider="gemini",
            model=self.model,
            duration_seconds=round(duration, 3),
            token_usage=None,
        )


class AIService:
    SUPPORTED_PROVIDERS = ("ollama", "gemini")

    def __init__(self):
        raw_provider = os.getenv("LLM_PROVIDER", "ollama")
        normalized = raw_provider.strip().lower()
        if normalized not in self.SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported LLM_PROVIDER '{raw_provider}'. Supported values: 'gemini', 'ollama'"
            )

        self.provider_name = normalized
        log_level_name = os.getenv("LLM_LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, log_level_name, logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        )
        logger.setLevel(log_level)

        if self.provider_name == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:8080")
            model = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
            timeout = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))
            self.provider = OllamaProvider(
                base_url=base_url,
                model=model,
                timeout_seconds=timeout,
            )
            logger.info(
                "AIService initialized with provider=ollama, model=%s, endpoint=%s, timeout=%.1fs",
                model,
                self.provider.sanitized_host,
                timeout,
            )
        elif self.provider_name == "gemini":
            api_key = os.getenv("GEMINI_API_KEY", "")
            model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
            self.provider = GeminiProvider(
                api_key=api_key,
                model=model,
            )
            logger.info(
                "AIService initialized with provider=gemini, model=%s, key_configured=%s",
                model,
                bool(api_key),
            )

    @property
    def model(self) -> str:
        return self.provider.model

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        feature_name: str = "general",
    ) -> AIResponse:
        return self.provider.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            feature_name=feature_name,
        )

    def get_status(self) -> Dict[str, Any]:
        health = self.provider.check_health()
        return {
            "llm_provider": self.provider_name,
            "model": self.provider.model,
            "provider_configured": True,
            "service_reachable": health.get("reachable", False),
            "model_available": health.get("model_available", False),
            "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
            "ollama_reachable": (
                health.get("reachable", False)
                if self.provider_name == "ollama"
                else self._check_ollama_quick()
            ),
            "error": health.get("error"),
        }

    def _check_ollama_quick(self) -> bool:
        url = os.getenv("OLLAMA_BASE_URL", "http://localhost:8080").rstrip("/") + "/api/tags"
        try:
            return requests.get(url, timeout=2).status_code == 200
        except Exception:
            return False


_global_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    global _global_ai_service
    if _global_ai_service is None:
        _global_ai_service = AIService()
    return _global_ai_service
