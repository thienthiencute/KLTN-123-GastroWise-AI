"""
HTTP-layer Contract Tests for Planning Service <-> AI Service Route Optimization:
POST /routes/optimize

Tests:
- Exact payload mapped by BE Planning Service AiApiClient.mapToCanonicalAiRequest
- Documented legacy aliases: lng->lon, restaurants->candidates, budget_vnd->budget,
  start_lat/start_lng->start_location, duration_mins->dining_duration_mins, open/close, start_time
- Empty candidate list -> HTTP 200 status="EMPTY"
- Missing required fields & invalid candidate types -> HTTP 422
- Dual stops & ordered_stops response contract
"""

import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

import main

TEST_AI_KEY = "test_m73_internal_ai_key_32chars_ok"
HEADERS = {"X-Internal-AI-Key": TEST_AI_KEY}


class TestPlanningContractHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app, raise_server_exceptions=False)

    def test_canonical_planning_acl_payload(self):
        """Matches exact RouteOptimizeCanonicalRequest sent by Planning AiApiClient."""
        payload = {
            "start_location": [10.7769, 106.7009],
            "start_time_mins": 660,
            "budget": 250000,
            "routing_mode": "motorbike",
            "desired_stops": 2,
            "candidates": [
                {
                    "id": "rest_a",
                    "name": "Phở Bò Gia Truyền",
                    "lat": 10.7750,
                    "lon": 106.7020,
                    "meal_type": "main",
                    "open_time": "08:00",
                    "close_time": "22:00",
                    "dining_duration_mins": 45,
                    "avg_price": 60000,
                    "rating": 8.8,
                },
                {
                    "id": "rest_b",
                    "name": "Chè Khúc Bạch",
                    "lat": 10.7780,
                    "lon": 106.7050,
                    "meal_type": "dessert",
                    "open_time": "10:00",
                    "close_time": "21:30",
                    "dining_duration_mins": 30,
                    "avg_price": 35000,
                    "rating": 4.7,
                },
            ],
        }
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}):
            resp = self.client.post("/routes/optimize", json=payload, headers=HEADERS)

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "SUCCESS")
        self.assertIsInstance(body["stops"], list)
        self.assertIsInstance(body["ordered_stops"], list)
        self.assertEqual(len(body["stops"]), 2)
        self.assertEqual(body["stops"], body["ordered_stops"])
        for s in body["stops"]:
            for key in (
                "id", "name", "lat", "lon", "order_index", "meal_type",
                "arrival_time", "departure_time", "dining_duration_mins",
                "transit_time_mins", "distance_to_next_km", "estimated_cost",
            ):
                self.assertIn(key, s)

    def test_legacy_aliases_payload_via_http(self):
        """Tests all documented legacy aliases: restaurants, start_lat/lng, budget_vnd, start_time, lng, open/close, duration_mins."""
        legacy_payload = {
            "start_lat": 10.7769,
            "start_lng": 106.7009,
            "start_time": "11:30",
            "budget_vnd": 300000,
            "routing_mode": "car",
            "desired_stops": 2,
            "restaurants": [
                {
                    "id": "legacy_1",
                    "lat": 10.7755,
                    "lng": 106.7025,
                    "open": "08:00",
                    "close": "22:00",
                    "duration_mins": 40,
                },
                {
                    "id": "legacy_2",
                    "name": "Cà Phê Sáng",
                    "lat": 10.7790,
                    "lng": 106.7040,
                    "open": "07:00",
                    "close": "23:00",
                    "duration_mins": 30,
                    "meal_type": "cafe",
                },
            ],
        }
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}):
            resp = self.client.post("/routes/optimize", json=legacy_payload, headers=HEADERS)

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "SUCCESS")
        self.assertEqual(body["routing_mode"], "car")
        self.assertEqual(len(body["stops"]), 2)
        # Name fallback applied to legacy_1
        ids_to_names = {s["id"]: s["name"] for s in body["stops"]}
        self.assertEqual(ids_to_names["legacy_1"], "Restaurant legacy_1")

    def test_empty_candidates_returns_empty_status(self):
        payload = {"start_location": [10.7769, 106.7009], "budget": 150000, "candidates": []}
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}):
            resp = self.client.post("/routes/optimize", json=payload, headers=HEADERS)

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "EMPTY")
        self.assertEqual(body["stops"], [])
        self.assertEqual(body["ordered_stops"], [])
        self.assertEqual(body["remaining_budget"], 150000)

    def test_invalid_candidate_or_missing_required_fields_returns_422(self):
        with patch.dict(os.environ, {"INTERNAL_AI_KEY": TEST_AI_KEY}):
            # Missing start_location
            r1 = self.client.post("/routes/optimize", json={"candidates": []}, headers=HEADERS)
            self.assertEqual(r1.status_code, 422)

            # Invalid candidate lat/lon type
            r2 = self.client.post(
                "/routes/optimize",
                json={
                    "start_location": [10.77, 106.70],
                    "candidates": [{"id": "bad", "name": "Bad Stop", "lat": "not-a-float", "lon": 106.7}],
                },
                headers=HEADERS,
            )
            self.assertEqual(r2.status_code, 422)


if __name__ == "__main__":
    unittest.main()
