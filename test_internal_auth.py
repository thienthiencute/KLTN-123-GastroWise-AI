import os
import unittest
import asyncio
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.core.auth import verify_internal_ai_key

class TestInternalAiAuth(unittest.TestCase):
    def test_missing_environment_variable_fails_closed(self):
        """Verify that when INTERNAL_AI_KEY is unset, authentication fails closed with HTTP 500."""
        orig = os.environ.get("INTERNAL_AI_KEY")
        try:
            if "INTERNAL_AI_KEY" in os.environ:
                del os.environ["INTERNAL_AI_KEY"]

            req = MagicMock()
            req.headers = {"X-Internal-AI-Key": "any_key"}

            with self.assertRaises(HTTPException) as cm:
                asyncio.run(verify_internal_ai_key(req))

            self.assertEqual(cm.exception.status_code, 500)
            self.assertIn("INTERNAL_AI_KEY is not configured", cm.exception.detail)
        finally:
            if orig is not None:
                os.environ["INTERNAL_AI_KEY"] = orig

    def test_missing_request_header_returns_401(self):
        """Verify that request without X-Internal-AI-Key header returns HTTP 401."""
        orig = os.environ.get("INTERNAL_AI_KEY")
        try:
            os.environ["INTERNAL_AI_KEY"] = "test_secret_key_12345"

            req = MagicMock()
            req.headers = {}

            with self.assertRaises(HTTPException) as cm:
                asyncio.run(verify_internal_ai_key(req))

            self.assertEqual(cm.exception.status_code, 401)
            self.assertIn("Missing X-Internal-AI-Key header", cm.exception.detail)
        finally:
            if orig is not None:
                os.environ["INTERNAL_AI_KEY"] = orig

    def test_invalid_key_returns_403(self):
        """Verify that request with invalid key returns HTTP 403."""
        orig = os.environ.get("INTERNAL_AI_KEY")
        try:
            os.environ["INTERNAL_AI_KEY"] = "test_secret_key_12345"

            req = MagicMock()
            req.headers = {"X-Internal-AI-Key": "wrong_spoofed_key"}

            with self.assertRaises(HTTPException) as cm:
                asyncio.run(verify_internal_ai_key(req))

            self.assertEqual(cm.exception.status_code, 403)
            self.assertIn("Invalid internal AI service key", cm.exception.detail)
        finally:
            if orig is not None:
                os.environ["INTERNAL_AI_KEY"] = orig

    def test_valid_key_passes(self):
        """Verify that request with exact valid key passes (returns True)."""
        orig = os.environ.get("INTERNAL_AI_KEY")
        try:
            os.environ["INTERNAL_AI_KEY"] = "test_secret_key_12345"

            req = MagicMock()
            req.headers = {"X-Internal-AI-Key": "test_secret_key_12345"}

            result = asyncio.run(verify_internal_ai_key(req))
            self.assertTrue(result)
        finally:
            if orig is not None:
                os.environ["INTERNAL_AI_KEY"] = orig

if __name__ == "__main__":
    unittest.main()
