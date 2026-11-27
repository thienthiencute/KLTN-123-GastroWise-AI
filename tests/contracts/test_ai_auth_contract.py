"""
HTTP-layer Contract Tests for AI Internal Mutual Authentication (X-Internal-AI-Key)
and OpenAPI Contract Snapshot Regression Protection.
"""

import json
import os
import unittest
from unittest.mock import patch
import pandas as pd
from fastapi.testclient import TestClient

import main

TEST_AI_KEY = "test_m73_internal_ai_key_32chars_ok"
SNAPSHOT_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "contract_snapshot.json"
)


class TestAiAuthContractHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app, raise_server_exceptions=False)
        cls.empty_df = pd.DataFrame(
            columns=["id", "name", "tags", "rating", "price", "lat", "lon", "district", "address"]
        )

    def test_health_endpoint_accessible_without_auth(self):
        with patch("main.get_dataset", return_value=self.empty_df):
            resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("status", body)
        self.assertIn("restaurants_loaded", body)

    def test_missing_auth_header_returns_401(self):
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}):
            for path, payload in [
                ("/recommend", {"query": "pho"}),
                ("/recommend/hybrid", {"user_id": "u1"}),
                ("/routes/optimize", {"start_location": [10.77, 106.70], "candidates": []}),
                ("/copilot/message", {"message": "xin chào"}),
                ("/analyze-sentiment", {"review": "ngon"}),
                ("/weather-recommend", {}),
                ("/cf/train", {"interactions": []}),
            ]:
                resp = self.client.post(path, json=payload)
                self.assertEqual(resp.status_code, 401, f"Expected 401 on {path}, got {resp.status_code}")
                self.assertEqual(resp.json()["detail"], "Missing X-Internal-AI-Key header")

    def test_incorrect_auth_header_returns_403(self):
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}):
            resp = self.client.post(
                "/recommend/hybrid",
                json={"user_id": "u1"},
                headers={"X-Internal-AI-Key": "wrong_key_attempt"},
            )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()["detail"], "Invalid internal AI service key")

    def test_missing_server_env_key_fails_closed_500(self):
        env_copy = dict(os.environ)
        env_copy.pop("INTERNAL_AI_KEY", None)
        with patch.dict(os.environ, env_copy, clear=True):
            resp = self.client.post(
                "/recommend/hybrid",
                json={"user_id": "u1"},
                headers={"X-Internal-AI-Key": TEST_AI_KEY},
            )
        self.assertEqual(resp.status_code, 500)
        self.assertIn("INTERNAL_AI_KEY is not configured", resp.json()["detail"])

    def test_valid_auth_header_succeeds_200(self):
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}), \
             patch("app.core.recommender.get_dataset", return_value=self.empty_df):
            resp = self.client.post(
                "/recommend/hybrid",
                json={"user_id": "u1"},
                headers={"X-Internal-AI-Key": TEST_AI_KEY},
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["total"], 0)

    def test_openapi_contract_snapshot_matches(self):
        """Regression guard preventing silent changes to paths, required fields, or property names."""
        with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
            expected = json.load(f)

        spec = main.app.openapi()
        actual = {
            "paths": {p: sorted(list(methods.keys())) for p, methods in sorted(spec["paths"].items())},
            "schemas": {
                name: {
                    "required": sorted(schema.get("required", [])),
                    "properties": sorted(list(schema.get("properties", {}).keys())),
                }
                for name, schema in sorted(spec["components"]["schemas"].items())
            },
        }
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
