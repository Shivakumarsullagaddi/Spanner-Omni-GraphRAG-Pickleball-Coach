import os
import unittest
from unittest.mock import patch, MagicMock
import requests

from ai_service import AIService, OllamaProvider, GeminiProvider, AIResponse


class TestProviderSelection(unittest.TestCase):
    def test_ollama_selection(self):
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "ollama",
                "OLLAMA_BASE_URL": "http://localhost:8080",
                "OLLAMA_MODEL": "gemma4:e2b",
            },
            clear=False,
        ):
            svc = AIService()
            self.assertEqual(svc.provider_name, "ollama")
            self.assertIsInstance(svc.provider, OllamaProvider)
            self.assertEqual(svc.model, "gemma4:e2b")

    def test_gemini_selection(self):
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "gemini",
                "GEMINI_API_KEY": "AIzaSyTestKeyForTestingOnly",
                "GEMINI_MODEL": "gemini-3.8-flash",
            },
            clear=False,
        ):
            with patch.object(GeminiProvider, "_init_client"):
                svc = AIService()
                self.assertEqual(svc.provider_name, "gemini")
                self.assertIsInstance(svc.provider, GeminiProvider)
                self.assertEqual(svc.model, "gemini-3.8-flash")

    def test_unsupported_provider(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "unsupported_llm"}, clear=False):
            with self.assertRaises(ValueError) as ctx:
                AIService()
            self.assertIn("Unsupported LLM_PROVIDER", str(ctx.exception))

    def test_case_insensitive_provider(self):
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "  OLLAMA  ",
                "OLLAMA_BASE_URL": "http://localhost:8080",
                "OLLAMA_MODEL": "gemma4:e2b",
            },
            clear=False,
        ):
            svc = AIService()
            self.assertEqual(svc.provider_name, "ollama")

    def test_missing_gemini_key(self):
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": ""},
            clear=False,
        ):
            with self.assertRaises(ValueError) as ctx:
                AIService()
            self.assertIn("GEMINI_API_KEY is required", str(ctx.exception))

    def test_ollama_does_not_initialize_gemini(self):
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "ollama",
                "GEMINI_API_KEY": "",
                "OLLAMA_BASE_URL": "http://localhost:8080",
                "OLLAMA_MODEL": "gemma4:e2b",
            },
            clear=False,
        ):
            with patch.object(GeminiProvider, "_init_client") as mock_init:
                svc = AIService()
                self.assertIsInstance(svc.provider, OllamaProvider)
                mock_init.assert_not_called()


class TestOllamaProvider(unittest.TestCase):
    def setUp(self):
        self.provider = OllamaProvider(
            base_url="http://localhost:8080",
            model="gemma4:e2b",
            timeout_seconds=5.0,
        )

    @patch("requests.post")
    def test_generate_text_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "model": "gemma4:e2b",
            "message": {
                "role": "assistant",
                "content": "Keep your paddle up at the kitchen line.",
            },
            "eval_count": 42,
        }
        mock_post.return_value = mock_resp

        res = self.provider.generate_text("How to dink?", feature_name="test_feature")
        self.assertIsInstance(res, AIResponse)
        self.assertEqual(res.provider, "ollama")
        self.assertEqual(res.model, "gemma4:e2b")
        self.assertEqual(res.text, "Keep your paddle up at the kitchen line.")
        self.assertEqual(res.token_usage, 42)
        self.assertGreaterEqual(res.duration_seconds, 0)

    @patch("requests.post")
    def test_generate_text_strips_thinking(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "model": "gemma4:e2b",
            "message": {
                "role": "assistant",
                "content": "<thought>thinking step</thought>Actual coaching advice.",
            },
            "eval_count": 30,
        }
        mock_post.return_value = mock_resp

        res = self.provider.generate_text("Prompt")
        self.assertEqual(res.text, "Actual coaching advice.")

    @patch("requests.post")
    def test_generate_text_connection_failure(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        with self.assertRaises(ConnectionError) as ctx:
            self.provider.generate_text("Prompt")
        self.assertIn("Cannot reach Ollama", str(ctx.exception))

    @patch("requests.post")
    def test_generate_text_timeout(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")
        with self.assertRaises(TimeoutError) as ctx:
            self.provider.generate_text("Prompt")
        self.assertIn("timed out", str(ctx.exception))

    @patch("requests.post")
    def test_generate_text_model_not_found(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = "model not found"
        mock_post.return_value = mock_resp

        with self.assertRaises(ValueError) as ctx:
            self.provider.generate_text("Prompt")
        self.assertIn("not found on server", str(ctx.exception))

    @patch("requests.get")
    def test_check_health_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "models": [{"name": "gemma4:e2b"}, {"name": "llama3:latest"}]
        }
        mock_get.return_value = mock_resp

        status = self.provider.check_health()
        self.assertTrue(status["reachable"])
        self.assertTrue(status["model_available"])
        self.assertIsNone(status["error"])

    @patch("requests.get")
    def test_check_health_unreachable(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("Refused")
        status = self.provider.check_health()
        self.assertFalse(status["reachable"])
        self.assertFalse(status["model_available"])
        self.assertIsNotNone(status["error"])


class TestGeminiProvider(unittest.TestCase):
    @patch.object(GeminiProvider, "_init_client")
    def test_generate_text_gemini(self, mock_init):
        provider = GeminiProvider(
            api_key="AIzaSyDummyTestKey",
            model="gemini-3.8-flash",
        )
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Target the opponent's backhand NVZ zone."
        mock_client.models.generate_content.return_value = mock_response
        provider.client = mock_client

        with patch("requests.post") as mock_ollama_post:
            res = provider.generate_text("How to win?", feature_name="gemini_test")
            mock_ollama_post.assert_not_called()

        self.assertEqual(res.provider, "gemini")
        self.assertEqual(res.model, "gemini-3.8-flash")
        self.assertEqual(res.text, "Target the opponent's backhand NVZ zone.")

    @patch.object(GeminiProvider, "_init_client")
    def test_gemini_failure_no_ollama_fallback(self, mock_init):
        provider = GeminiProvider(
            api_key="AIzaSyDummyTestKey",
            model="gemini-3.8-flash",
        )
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Gemini quota exceeded")
        provider.client = mock_client

        with patch("requests.post") as mock_ollama_post:
            with self.assertRaises(RuntimeError) as ctx:
                provider.generate_text("Prompt")
            mock_ollama_post.assert_not_called()

        self.assertIn("Gemini API request failed", str(ctx.exception))


class TestSecurityAndLogging(unittest.TestCase):
    def test_logs_do_not_contain_api_key(self):
        secret_key = "AIzaSySuperSecretKey123456789"
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "gemini",
                "GEMINI_API_KEY": secret_key,
                "GEMINI_MODEL": "gemini-3.8-flash",
            },
            clear=False,
        ):
            with patch.object(GeminiProvider, "_init_client"):
                with self.assertLogs("pickleball.ai", level="INFO") as log_capture:
                    svc = AIService()
                    mock_client = MagicMock()
                    mock_resp = MagicMock()
                    mock_resp.text = "Tactical response."
                    mock_client.models.generate_content.return_value = mock_resp
                    svc.provider.client = mock_client
                    svc.generate("Test prompt", feature_name="security_check")

                    for record in log_capture.output:
                        self.assertNotIn(secret_key, record)


class TestAppEndpoints(unittest.TestCase):
    def setUp(self):
        from app import app
        app.testing = True
        self.client = app.test_client()

    def test_status_endpoint(self):
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("llm_provider", data)
        self.assertIn("model", data)
        self.assertIn("provider_configured", data)
        self.assertIn("service_reachable", data)
        self.assertIn("spanner_connected", data)
        self.assertIn("counts", data)

    def test_courts_endpoint(self):
        res = self.client.get("/api/courts")
        self.assertEqual(res.status_code, 200)
        courts = res.get_json()
        self.assertIsInstance(courts, list)
        self.assertGreaterEqual(len(courts), 1)

    def test_bookings_endpoint(self):
        res = self.client.get("/api/bookings")
        self.assertEqual(res.status_code, 200)
        bookings = res.get_json()
        self.assertIsInstance(bookings, list)

    def test_matches_endpoint(self):
        res = self.client.get("/api/matches")
        self.assertEqual(res.status_code, 200)
        matches = res.get_json()
        self.assertIsInstance(matches, list)


if __name__ == "__main__":
    unittest.main()
