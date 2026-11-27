"""
M10.0 Regression Tests — MongoDB Data Readiness, Schema Mapping, Rating Normalization,
Error Status Exposure, and Log Sanitization.
"""

import math
import os
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError

import main
from app.config import build_mongo_uri_from_env
from app.core.rating_normalizer import (
    DEFAULT_NEUTRAL_RATING,
    RatingScale,
    detect_restaurant_rating_scale,
    normalize_rating,
    normalize_restaurant_dict,
)
from app.core.recommender import recommend_hybrid, recommend_restaurants
from app.db import mongo as mongo_mod
from app.schemas.recommendation import HybridRecommendRequest, RecommendRequest


class TestMongoConfigAndSanitization(unittest.TestCase):
    def test_build_mongo_uri_from_discrete_docker_env(self):
        env = {
            "AI_DB_USER": "gastro_ai_reader",
            "AI_DB_PASSWORD": "p@ss:word/123",
            "MONGO_HOST": "mongo-test",
            "MONGO_PORT": "27017",
            "MONGO_AUTH_SOURCE": "gastro_core_test",
        }
        with patch.dict(os.environ, env, clear=True):
            uri = build_mongo_uri_from_env()
        self.assertIn("gastro_ai_reader:p%40ss%3Aword%2F123@mongo-test:27017/", uri)
        self.assertIn("authSource=gastro_core_test", uri)

    def test_sanitize_log_message_masks_uris_and_passwords(self):
        raw = "Authentication failed for mongodb://gastro_ai_reader:SuperSecret123@mongo-test:27017/gastro_core_test password=LeakMe"
        masked = mongo_mod.sanitize_log_message(raw)
        self.assertNotIn("SuperSecret123", masked)
        self.assertNotIn("LeakMe", masked)
        self.assertIn("mongodb://[REDACTED_AUTH]@mongo-test:27017", masked)
        self.assertIn("password=[REDACTED]", masked)


class TestMongoReadinessAndSchemaMapping(unittest.TestCase):
    def setUp(self):
        mongo_mod.df = None
        mongo_mod.tfidf_vectorizer = None
        mongo_mod._last_db_error = None
        mongo_mod._dataset_status = mongo_mod.DATA_STATUS_DB_UNAVAILABLE

    def test_missing_uri_fails_closed_as_database_unavailable(self):
        with patch.object(mongo_mod, "MONGO_URI", None):
            with self.assertRaises(mongo_mod.DatabaseLoadError):
                mongo_mod.load_dataset_from_mongo()
        self.assertEqual(mongo_mod.get_dataset_status(), mongo_mod.DATA_STATUS_DB_UNAVAILABLE)

        client = TestClient(main.app, raise_server_exceptions=False)
        with patch.object(mongo_mod, "MONGO_URI", None):
            resp = client.get("/")
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.json()["data_status"], mongo_mod.DATA_STATUS_DB_UNAVAILABLE)

    def test_connection_or_auth_failure_not_masked_as_empty_dataset(self):
        mock_client = MagicMock()
        mock_client.admin.command.side_effect = OperationFailure("bad auth for mongodb://user:SecretPW@mongo-test:27017")
        with patch.object(mongo_mod, "MONGO_URI", "mongodb://user:SecretPW@mongo-test:27017/gastro_core_test"), \
             patch.object(mongo_mod, "MongoClient", return_value=mock_client):
            with self.assertRaises(mongo_mod.DatabaseLoadError) as ctx:
                mongo_mod.load_dataset_from_mongo()
        self.assertNotIn("SecretPW", str(ctx.exception))
        self.assertEqual(mongo_mod.get_dataset_status(), mongo_mod.DATA_STATUS_DB_UNAVAILABLE)

        mock_client_timeout = MagicMock()
        mock_client_timeout.admin.command.side_effect = ServerSelectionTimeoutError("timed out")
        client = TestClient(main.app, raise_server_exceptions=False)
        with patch.object(mongo_mod, "MONGO_URI", "mongodb://user:SecretPW@mongo-test:27017/gastro_core_test"), \
             patch.object(mongo_mod, "MongoClient", return_value=mock_client_timeout):
            resp = client.get("/")
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.json()["data_status"], mongo_mod.DATA_STATUS_DB_UNAVAILABLE)

    def test_authenticated_empty_collection_reports_empty_dataset(self):
        mock_col = MagicMock()
        mock_col.find.return_value = []
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_col
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_client.__getitem__.return_value = mock_db

        with patch.object(mongo_mod, "MONGO_URI", "mongodb://user:pw@mongo-test:27017/gastro_core_test"), \
             patch.object(mongo_mod, "MongoClient", return_value=mock_client):
            loaded = mongo_mod.load_dataset_from_mongo()
            self.assertFalse(loaded)
            self.assertEqual(mongo_mod.get_dataset_status(), mongo_mod.DATA_STATUS_EMPTY)
            client = TestClient(main.app, raise_server_exceptions=False)
            resp = client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data_status"], mongo_mod.DATA_STATUS_EMPTY)
        self.assertEqual(resp.json()["restaurants_loaded"], 0)

    def test_all_invalid_documents_raise_data_validation_failed(self):
        mock_col = MagicMock()
        mock_col.find.return_value = [
            {"_id": "bad1"},  # missing name
            {"name": "No ID Place"},  # missing _id
        ]
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_col
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_client.__getitem__.return_value = mock_db

        with patch.object(mongo_mod, "MONGO_URI", "mongodb://user:pw@mongo-test:27017/gastro_core_test"), \
             patch.object(mongo_mod, "MongoClient", return_value=mock_client):
            with self.assertRaises(mongo_mod.DatasetValidationError):
                mongo_mod.load_dataset_from_mongo()
        self.assertEqual(mongo_mod.get_dataset_status(), mongo_mod.DATA_STATUS_VALIDATION_FAILED)

    def test_mixed_valid_invalid_dedup_coords_price_and_rating_mapping(self):
        raw_docs = [
            {
                "_id": "r1",
                "tenQuan": "Phở Hà Nội",
                "diemTrungBinh": 8.6,
                "diemChatLuong": 8.8,
                "reviewsCount": 0,
                "giaCa": "65.000đ",
                "diaChi": "10 Lê Lợi, Quận 1, TP.HCM",
                "location": {"type": "Point", "coordinates": [106.7011, 10.7755]},
                "tags": ["phở bò", "nóng"],
            },
            {
                "_id": "r1",  # duplicate ID -> skipped
                "tenQuan": "Phở Hà Nội Dup ID",
            },
            {
                "_id": "r2",
                "name": "Cơm Chay An Lạc",
                "diemTrungBinh": 4.4,
                "reviewsCount": 12,
                "price": -20000,  # negative -> clamped 0.0
                "address": None,
                "location": None,  # un-geocoded -> (0.0, 0.0), coords_valid=False
                "tags": None,
            },
            {
                "_id": "r3_bad_coords",
                "tenQuan": "Quán Tọa Độ Sai",
                "diemTrungBinh": None,
                "lat": 999.0,  # out-of-range lat -> coerced safely
                "lon": 106.70,
                "tags": "bún chả, hà nội",
                "diaChi": "25 Võ Văn Tần, Quận 3",
            },
            {
                "_id": "r4_missing_name",  # invalid -> rejected without crashing valid rows
            },
        ]

        mock_col = MagicMock()
        mock_col.find.return_value = raw_docs
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_col
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_client.__getitem__.return_value = mock_db

        with patch.object(mongo_mod, "MONGO_URI", "mongodb://user:pw@mongo-test:27017/gastro_core_test"), \
             patch.object(mongo_mod, "MongoClient", return_value=mock_client):
            ok = mongo_mod.load_dataset_from_mongo()
            self.assertTrue(ok)
            self.assertEqual(mongo_mod.get_dataset_status(), mongo_mod.DATA_STATUS_READY)

        summary = mongo_mod.get_validation_summary()
        self.assertEqual(summary["raw_count"], 5)
        self.assertEqual(summary["loaded_count"], 3)
        self.assertEqual(summary["rejected_count"], 1)
        self.assertEqual(summary["duplicates_skipped"], 1)
        self.assertEqual(summary["invalid_coordinates_count"], 2)
        self.assertEqual(summary["missing_tags_count"], 1)
        self.assertEqual(summary["missing_address_count"], 1)

        loaded_df = mongo_mod.get_dataset()
        r1 = loaded_df[loaded_df["id"] == "r1"].iloc[0]
        self.assertEqual(r1["rating"], 4.3)
        self.assertEqual(r1["raw_rating"], 8.6)
        self.assertEqual(r1["price"], 65000.0)
        self.assertAlmostEqual(r1["lat"], 10.7755)
        self.assertAlmostEqual(r1["lon"], 106.7011)
        self.assertTrue(bool(r1["coords_valid"]))

        r2 = loaded_df[loaded_df["id"] == "r2"].iloc[0]
        self.assertEqual(r2["rating"], 4.4)
        self.assertEqual(r2["price"], 0.0)
        self.assertEqual(r2["tags"], "")
        self.assertEqual(r2["address"], "")
        self.assertFalse(bool(r2["coords_valid"]))

        # Verify recommendation endpoints work against this loaded Mongo dataset
        rec = recommend_restaurants(RecommendRequest(query="phở bò", user_gps=[10.7769, 106.7009]))
        self.assertGreaterEqual(len(rec["scores"]), 1)
        hyb = recommend_hybrid(HybridRecommendRequest(user_gps=[10.7769, 106.7009], limit=5))
        self.assertEqual(hyb.total, 3)


class TestRatingNormalizationExtended(unittest.TestCase):
    def test_all_scales_null_out_of_range_and_idempotency(self):
        self.assertEqual(normalize_rating(9.4, scale=RatingScale.SCALE_10), 4.7)
        self.assertEqual(normalize_rating(4.2, scale=RatingScale.SCALE_5), 4.2)
        self.assertEqual(normalize_rating(None), DEFAULT_NEUTRAL_RATING)
        self.assertEqual(normalize_rating(float("nan")), DEFAULT_NEUTRAL_RATING)
        self.assertEqual(normalize_rating(-3.5), 0.0)
        self.assertEqual(normalize_rating(25.0), 5.0)

        doc_with_explicit_scale = {"tenQuan": "Foody Low", "diemTrungBinh": 4.0, "ratingScale": "10_point"}
        scale, raw = detect_restaurant_rating_scale(doc_with_explicit_scale)
        self.assertEqual(scale, RatingScale.SCALE_10)
        normalized = normalize_restaurant_dict(doc_with_explicit_scale)
        self.assertEqual(normalized["rating"], 2.0)
        self.assertEqual(normalized["raw_rating"], 4.0)

        # Calling normalize_restaurant_dict a second time must not re-divide
        normalized_twice = normalize_restaurant_dict(normalized)
        self.assertEqual(normalized_twice["rating"], 2.0)
        self.assertEqual(normalized_twice["raw_rating"], 4.0)


if __name__ == "__main__":
    unittest.main()
