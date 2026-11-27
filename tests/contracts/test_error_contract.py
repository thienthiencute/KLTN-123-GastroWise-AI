"""
HTTP-layer Contract Tests for Error Handling, Validation (422), Malformed JSON,
Vision Unavailability (503), and Live Localhost Uvicorn HTTP Server Integration.
"""

import asyncio
import os
import unittest
from unittest.mock import patch
import httpx
import pandas as pd
from fastapi.testclient import TestClient

import main

TEST_AI_KEY = "test_m73_internal_ai_key_32chars_ok"
HEADERS = {"X-Internal-AI-Key": TEST_AI_KEY}


class TestErrorAndLiveHttpContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app, raise_server_exceptions=False)

    def test_missing_required_fields_returns_422(self):
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}):
            for path, bad_body in [
                ("/recommend", {}),
                ("/copilot/message", {}),
                ("/analyze-sentiment", {}),
                ("/cf/train", {}),
            ]:
                resp = self.client.post(path, json=bad_body, headers=HEADERS)
                self.assertEqual(resp.status_code, 422, f"Expected 422 on {path}")
                self.assertIn("detail", resp.json())

    def test_invalid_data_types_returns_422(self):
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}):
            resp = self.client.post(
                "/recommend/hybrid",
                json={"limit": "ten", "max_price": "cheap", "user_gps": "bad-gps"},
                headers=HEADERS,
            )
        self.assertEqual(resp.status_code, 422)
        self.assertIsInstance(resp.json()["detail"], list)

    def test_malformed_json_returns_422(self):
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}):
            resp = self.client.post(
                "/recommend",
                content="{bad json payload",
                headers={**HEADERS, "Content-Type": "application/json"},
            )
        self.assertEqual(resp.status_code, 422)

    def test_predict_food_when_yolo_unavailable_returns_503(self):
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}), \
             patch("app.core.vision_service.get_yolo_model", return_value=None):
            resp = self.client.post(
                "/predict-food",
                files={"file": ("dish.jpg", b"fake-jpeg-bytes", "image/jpeg")},
                headers=HEADERS,
            )
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.json()["detail"], "Model AI chưa sẵn sàng")

    def test_httpx_asgi_transport_full_http_roundtrip(self):
        """
        Exercises full ASGI HTTP protocol cycle using httpx.AsyncClient + httpx.ASGITransport
        (headers, JSON encoding/decoding, status codes, auth, hybrid recommend, route optimize).
        """
        fixture_df = pd.DataFrame([
            {
                "id": "asgi_r1",
                "name": "Phở Bò ASGI Test",
                "tags": "phở bò nóng",
                "rating": 4.8,
                "price": 60000,
                "lat": 10.7769,
                "lon": 106.7009,
                "address": "1 Lê Lợi, Quận 1",
                "district": "Quận 1",
            }
        ])

        async def _run_calls():
            transport = httpx.ASGITransport(app=main.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://ai-service:5000") as client:
                health = await client.get("/")
                self.assertEqual(health.status_code, 200)

                unauth = await client.post("/recommend/hybrid", json={"user_id": "u1"})
                self.assertEqual(unauth.status_code, 401)

                hyb = await client.post(
                    "/recommend/hybrid",
                    json={"user_id": "u1", "user_gps": [10.7769, 106.7009], "limit": 5},
                    headers=HEADERS,
                )
                self.assertEqual(hyb.status_code, 200)
                self.assertEqual(hyb.json()["items"][0]["id"], "asgi_r1")

                route = await client.post(
                    "/routes/optimize",
                    json={
                        "start_location": [10.7769, 106.7009],
                        "candidates": [{"id": "c1", "name": "Stop 1", "lat": 10.775, "lon": 106.702}],
                    },
                    headers=HEADERS,
                )
                self.assertEqual(route.status_code, 200)
                self.assertEqual(route.json()["status"], "SUCCESS")

        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}), \
             patch("main.get_dataset", return_value=fixture_df), \
             patch("app.core.recommender.get_dataset", return_value=fixture_df):
            asyncio.run(_run_calls())


if __name__ == "__main__":
    unittest.main()
