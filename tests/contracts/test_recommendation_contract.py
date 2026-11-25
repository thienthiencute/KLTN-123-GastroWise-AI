"""
HTTP-layer Contract Tests for Backend Core Service <-> AI Service Endpoints:
- /recommend & /v1/recommendation/recommend
- /recommend/hybrid & /v1/recommendation/recommend/hybrid
- /cf/train & /v1/recommendation/cf/train
- /weather-recommend
- /copilot/message & /v1/copilot/message
- /analyze-sentiment
"""

import os
import unittest
from unittest.mock import patch
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from fastapi.testclient import TestClient

import main

TEST_AI_KEY = "test_m73_internal_ai_key_32chars_ok"
HEADERS = {"X-Internal-AI-Key": TEST_AI_KEY}


def _build_fixture_catalog() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "id": "65f1a0000000000000000001",
            "name": "Phở Bò Gia Truyền",
            "tags": "phở bò nước dùng nóng truyền thống",
            "rating": 4.8,
            "price": 60000,
            "lat": 10.7769,
            "lon": 106.7009,
            "address": "15 Hai Bà Trưng, Quận 1",
            "district": "Quận 1",
        },
        {
            "id": "65f1a0000000000000000002",
            "name": "Cơm Chay Thanh Lương",
            "tags": "cơm chay vegan thanh đạm rau củ",
            "rating": 4.6,
            "price": 45000,
            "lat": 10.7775,
            "lon": 106.7012,
            "address": "22 Nguyễn Huệ, Quận 1",
            "district": "Quận 1",
        },
        {
            "id": "65f1a0000000000000000003",
            "name": "Lẩu Thái Khun Thai",
            "tags": "lẩu thái cay sa tế hải sản",
            "rating": 4.5,
            "price": 180000,
            "lat": 10.7780,
            "lon": 106.7020,
            "address": "123 Lê Lợi, Quận 1",
            "district": "Quận 1",
        },
    ])


class TestRecommendationContractHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app, raise_server_exceptions=False)
        cls.catalog_df = _build_fixture_catalog()
        cls.vec = TfidfVectorizer()
        cls.vec.fit(cls.catalog_df["tags"])

    def test_hybrid_recommend_backend_core_payload(self):
        """Matches exact payload constructed by Core RestaurantsService.getPersonalizedRecommendations."""
        payload = {
            "user_id": "65f1b0000000000000000099",
            "limit": 10,
            "weather_type": "rainy",
            "temperature": 23.0,
            "dietary_exclusions": ["chay"],
            "user_gps": [10.7769, 106.7009],
            "taste_vector": [0.2, 0.3, 0.2, 0.4, 0.8, 0.1],
            "max_price": 100000,
        }
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}), \
             patch("app.core.recommender.get_dataset", return_value=self.catalog_df):
            resp = self.client.post("/recommend/hybrid", json=payload, headers=HEADERS)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total", data)
        self.assertIn("is_cold_start", data)
        self.assertIn("applied_weights", data)
        self.assertIn("items", data)
        self.assertEqual(data["total"], 1)
        item = data["items"][0]
        self.assertEqual(item["id"], "65f1a0000000000000000002")
        for key in ("id", "name", "tags", "score", "taste_score", "cf_score", "env_score", "distance_km", "price", "match_reasons", "explanation"):
            self.assertIn(key, item)

    def test_hybrid_recommend_null_optionals_and_empty_results(self):
        payload = {
            "user_id": None,
            "user_gps": None,
            "taste_vector": None,
            "dietary_exclusions": None,
            "weather_type": None,
            "temperature": None,
            "max_price": 5000,  # strict budget matching 0 restaurants
            "limit": 5,
        }
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}), \
             patch("app.core.recommender.get_dataset", return_value=self.catalog_df):
            resp = self.client.post("/recommend/hybrid", json=payload, headers=HEADERS)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total"], 0)
        self.assertEqual(data["items"], [])

    def test_hybrid_recommend_invalid_gps_and_budget_boundary(self):
        # GPS list with wrong element count (1 element) -> safe fallback without crash
        payload_short_gps = {"user_gps": [10.7769], "max_price": 45000}
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}), \
             patch("app.core.recommender.get_dataset", return_value=self.catalog_df):
            resp = self.client.post("/recommend/hybrid", json=payload_short_gps, headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["total"], 1)
        self.assertEqual(resp.json()["items"][0]["price"], 45000)

        # Extreme out-of-range GPS coordinates -> safe distance handling, no 500/NaN
        payload_bad_coords = {"user_gps": [999.0, 999.0], "limit": 5}
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}), \
             patch("app.core.recommender.get_dataset", return_value=self.catalog_df):
            resp2 = self.client.post("/recommend/hybrid", json=payload_bad_coords, headers=HEADERS)
        self.assertEqual(resp2.status_code, 200)

    def test_recommend_search_backend_core_payload_and_dual_route(self):
        """Matches RestaurantsService.findAll payload -> POST /recommend & /v1/recommendation/recommend."""
        payload = {"query": "phở bò", "user_gps": [10.7769, 106.7009]}
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}), \
             patch("app.core.recommender.get_dataset", return_value=self.catalog_df), \
             patch("app.core.recommender.get_vectorizer", return_value=self.vec):
            r1 = self.client.post("/recommend", json=payload, headers=HEADERS)
            r2 = self.client.post("/v1/recommendation/recommend", json=payload, headers=HEADERS)

        for resp in (r1, r2):
            self.assertEqual(resp.status_code, 200)
            body = resp.json()
            self.assertIn("sort_by", body)
            self.assertIn("scores", body)
            self.assertGreater(len(body["scores"]), 0)
            self.assertEqual(body["scores"][0]["id"], "65f1a0000000000000000001")

    def test_cf_train_weather_sentiment_and_copilot_contracts(self):
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}), \
             patch("app.core.recommender.get_dataset", return_value=self.catalog_df), \
             patch("app.core.recommender.get_vectorizer", return_value=self.vec), \
             patch("app.core.weather_service.get_realtime_weather", return_value=(23.5, 61)):
            cf_resp = self.client.post(
                "/cf/train",
                json={"interactions": [
                    {"userId": "u1", "targetId": "r1", "eventType": "REVIEW", "rating": 5.0},
                    {"userId": "u2", "targetId": "r2", "eventType": "CLICK"},
                ]},
                headers=HEADERS,
            )
            self.assertEqual(cf_resp.status_code, 200)
            self.assertTrue(cf_resp.json()["success"])

            w_resp = self.client.post(
                "/weather-recommend",
                json={"user_gps": [10.7769, 106.7009]},
                headers=HEADERS,
            )
            self.assertEqual(w_resp.status_code, 200)
            self.assertEqual(w_resp.json()["weather"]["weather_type"], "rainy")

            s_resp = self.client.post(
                "/analyze-sentiment",
                json={"review": "Quán ngon, sạch sẽ, nhân viên nhiệt tình"},
                headers=HEADERS,
            )
            self.assertEqual(s_resp.status_code, 200)
            self.assertEqual(s_resp.json()["label"], "POSITIVE")
            self.assertIn("hashtags", s_resp.json())

            c_resp = self.client.post(
                "/copilot/message",
                json={"message": "bánh mì có bao nhiêu calo?", "user_gps": [10.7769, 106.7009]},
                headers=HEADERS,
            )
            self.assertEqual(c_resp.status_code, 200)
            self.assertEqual(c_resp.json()["intent"], "ask_nutrition")
            self.assertIn("action_card", c_resp.json())


if __name__ == "__main__":
    unittest.main()
