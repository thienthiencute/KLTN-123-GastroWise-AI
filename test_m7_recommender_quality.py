import math
import unittest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch

from app.core.rating_normalizer import (
    normalize_rating,
    detect_restaurant_rating_scale,
    normalize_restaurant_dict,
    RatingScale,
    DEFAULT_NEUTRAL_RATING
)
from app.core.recommender import (
    recommend_restaurants,
    recommend_hybrid,
    compute_restaurant_flavor_vector,
    compute_vector_cosine,
    compute_env_context
)
from app.schemas.recommendation import (
    RecommendRequest,
    HybridRecommendRequest,
    HybridRecommendResponse
)
from app.core.vision_service import preprocess_image_clahe
from PIL import Image

class TestRatingScaleNormalization(unittest.TestCase):
    """
    Test suite for ISSUE-06: Rating Scale Normalization
    Covers: 10-point, 5-point, missing, null, invalid, boundary values, and double normalization.
    """

    def test_ten_point_scale_normalization(self):
        """Test explicit 10-point scale normalization: maps [0, 10] to [0, 5]."""
        self.assertEqual(normalize_rating(10.0, scale=RatingScale.SCALE_10), 5.0)
        self.assertEqual(normalize_rating(8.4, scale=RatingScale.SCALE_10), 4.2)
        self.assertEqual(normalize_rating(7.5, scale=RatingScale.SCALE_10), 3.8)
        self.assertEqual(normalize_rating(6.0, scale=RatingScale.SCALE_10), 3.0)
        self.assertEqual(normalize_rating(5.0, scale=RatingScale.SCALE_10), 2.5)
        self.assertEqual(normalize_rating(4.0, scale=RatingScale.SCALE_10), 2.0)
        self.assertEqual(normalize_rating(1.0, scale=RatingScale.SCALE_10), 0.5)
        self.assertEqual(normalize_rating(0.0, scale=RatingScale.SCALE_10), 0.0)

    def test_five_point_scale_preservation(self):
        """Test explicit 5-point scale: preserves values in [0, 5]."""
        self.assertEqual(normalize_rating(5.0, scale=RatingScale.SCALE_5), 5.0)
        self.assertEqual(normalize_rating(4.8, scale=RatingScale.SCALE_5), 4.8)
        self.assertEqual(normalize_rating(3.5, scale=RatingScale.SCALE_5), 3.5)
        self.assertEqual(normalize_rating(2.0, scale=RatingScale.SCALE_5), 2.0)
        self.assertEqual(normalize_rating(1.0, scale=RatingScale.SCALE_5), 1.0)
        self.assertEqual(normalize_rating(0.0, scale=RatingScale.SCALE_5), 0.0)

    def test_auto_detection_scale(self):
        """Test auto-detection: values > 5.0 are treated as 10-point scale."""
        self.assertEqual(normalize_rating(9.0, scale=RatingScale.AUTO), 4.5)
        self.assertEqual(normalize_rating(8.0, scale=RatingScale.AUTO), 4.0)
        self.assertEqual(normalize_rating(7.0, scale=RatingScale.AUTO), 3.5)
        self.assertEqual(normalize_rating(6.0, scale=RatingScale.AUTO), 3.0)
        self.assertEqual(normalize_rating(4.5, scale=RatingScale.AUTO), 4.5)
        self.assertEqual(normalize_rating(3.0, scale=RatingScale.AUTO), 3.0)

    def test_missing_and_null_ratings(self):
        """Test handling of None, NaN, empty strings, and non-numeric values."""
        self.assertEqual(normalize_rating(None), DEFAULT_NEUTRAL_RATING)
        self.assertEqual(normalize_rating(float('nan')), DEFAULT_NEUTRAL_RATING)
        self.assertEqual(normalize_rating(float('inf')), DEFAULT_NEUTRAL_RATING)
        self.assertEqual(normalize_rating(float('-inf')), DEFAULT_NEUTRAL_RATING)
        self.assertEqual(normalize_rating(True), DEFAULT_NEUTRAL_RATING)
        self.assertEqual(normalize_rating(False), DEFAULT_NEUTRAL_RATING)
        self.assertEqual(normalize_rating(math.nan), DEFAULT_NEUTRAL_RATING)
        self.assertEqual(normalize_rating(""), DEFAULT_NEUTRAL_RATING)
        self.assertEqual(normalize_rating("N/A"), DEFAULT_NEUTRAL_RATING)
        self.assertEqual(normalize_rating("unrated"), DEFAULT_NEUTRAL_RATING)

    def test_invalid_and_out_of_range_ratings(self):
        """Test handling of negative values and values exceeding maximum scale."""
        # Negative ratings clamped to 0.0
        self.assertEqual(normalize_rating(-1.0), 0.0)
        self.assertEqual(normalize_rating(-5.5), 0.0)
        # Out-of-range ratings clamped to max 5.0
        self.assertEqual(normalize_rating(12.0), 5.0)
        self.assertEqual(normalize_rating(100.0), 5.0)

    def test_boundary_values(self):
        """Test exact boundary transitions."""
        self.assertEqual(normalize_rating(0.0), 0.0)
        self.assertEqual(normalize_rating(5.0), 5.0)
        self.assertEqual(normalize_rating(5.001, scale=RatingScale.AUTO), 2.5)
        self.assertEqual(normalize_rating(10.0, scale=RatingScale.AUTO), 5.0)

    def test_double_normalization_prevention(self):
        """Test that already-normalized ratings are not divided by 2 a second time."""
        # First normalization (10-point 8.4 -> 4.2)
        norm_1 = normalize_rating(8.4, scale=RatingScale.SCALE_10)
        self.assertEqual(norm_1, 4.2)
        # Second normalization with is_already_normalized=True
        norm_2 = normalize_rating(norm_1, is_already_normalized=True)
        self.assertEqual(norm_2, 4.2)
        self.assertNotEqual(norm_2, 2.1)

    def test_restaurant_doc_scale_detection(self):
        """Test metadata-based scale detection for restaurant documents."""
        # Case 1: Foody crawler document with subscores and raw 4.0/10
        foody_doc = {
            "tenQuan": "Quán Bún Bò",
            "diemTrungBinh": 4.0,
            "diemChatLuong": 4.0,
            "diemViTri": 4.0,
            "reviewsCount": 0
        }
        scale, raw_val = detect_restaurant_rating_scale(foody_doc)
        self.assertEqual(scale, RatingScale.SCALE_10)
        self.assertEqual(raw_val, 4.0)
        normalized_doc = normalize_restaurant_dict(foody_doc)
        self.assertEqual(normalized_doc['rating'], 2.0)
        self.assertEqual(normalized_doc['raw_rating'], 4.0)

        # Case 2: GastroWise user-reviewed restaurant (reviewsCount > 0, avg 4.0)
        user_reviewed_doc = {
            "tenQuan": "Cơm Tấm Ba Ghiền",
            "diemTrungBinh": 4.0,
            "reviewsCount": 15
        }
        scale_user, raw_user = detect_restaurant_rating_scale(user_reviewed_doc)
        self.assertEqual(scale_user, RatingScale.SCALE_5)
        self.assertEqual(raw_user, 4.0)
        normalized_user_doc = normalize_restaurant_dict(user_reviewed_doc)
        self.assertEqual(normalized_user_doc['rating'], 4.0)

        # Case 3: Foody 8.0/10 -> 4.0/5 and idempotency when both diemTrungBinh and rating exist
        foody_8_doc = {
            "tenQuan": "Phở Hòa",
            "diemTrungBinh": 8.0,
            "diemChatLuong": 8.2,
            "reviewsCount": 0
        }
        norm_8 = normalize_restaurant_dict(foody_8_doc)
        self.assertEqual(norm_8['rating'], 4.0)
        self.assertEqual(norm_8['raw_rating'], 8.0)
        # Re-detecting scale on normalized doc must preserve 4.0 and not re-read 8.0
        scale_recheck, val_recheck = detect_restaurant_rating_scale(norm_8)
        self.assertEqual(scale_recheck, RatingScale.SCALE_5)
        self.assertEqual(val_recheck, 4.0)

        # Case 4: Heterogeneous DataFrame NaN handling (reviewsCount=NaN on Foody doc with 4.0/10)
        foody_nan_rev_doc = {
            "tenQuan": "Quán Hủ Tiếu",
            "diemTrungBinh": 4.0,
            "diemChatLuong": 4.2,
            "reviewsCount": float('nan')
        }
        scale_nan_rev, raw_nan_rev = detect_restaurant_rating_scale(foody_nan_rev_doc)
        self.assertEqual(scale_nan_rev, RatingScale.SCALE_10)
        self.assertEqual(normalize_rating(raw_nan_rev, scale=scale_nan_rev), 2.0)

        # Case 5: Non-Foody doc with NaN subscores and reviewsCount=5 must stay SCALE_5
        gw_nan_sub_doc = {
            "tenQuan": "Quán Bún Đậu",
            "diemTrungBinh": 4.0,
            "diemChatLuong": float('nan'),
            "reviewsCount": 5
        }
        scale_gw_nan, raw_gw_nan = detect_restaurant_rating_scale(gw_nan_sub_doc)
        self.assertEqual(scale_gw_nan, RatingScale.SCALE_5)
        self.assertEqual(normalize_rating(raw_gw_nan, scale=scale_gw_nan), 4.0)


class TestCv2ImportAndResilience(unittest.TestCase):
    """
    Test suite for ISSUE-11: CV2 Import and Test Environment
    Ensures vision service can gracefully operate even when cv2 is not available.
    """

    def test_clahe_preprocessing_without_cv2(self):
        """Verify that preprocess_image_clahe falls back to returning the original image if cv2 is None."""
        test_img = Image.new('RGB', (100, 100), color='red')
        with patch('app.core.vision_service.cv2', None):
            result_img = preprocess_image_clahe(test_img)
            self.assertIsNotNone(result_img)
            self.assertEqual(result_img.size, test_img.size)

    def test_clahe_preprocessing_with_cv2(self):
        """Verify that preprocess_image_clahe enhances contrast when cv2 is available."""
        test_img = Image.new('RGB', (64, 64), color='blue')
        result_img = preprocess_image_clahe(test_img)
        self.assertIsNotNone(result_img)
        self.assertEqual(result_img.size, (64, 64))

    def test_main_and_vision_import_without_cv2(self):
        """Verify that main app and vision_service import and initialize cleanly when cv2 is unavailable."""
        import importlib
        import sys
        import app.core.vision_service as vs
        with patch.dict(sys.modules, {'cv2': None}):
            importlib.reload(vs)
            import main as app_main
            importlib.reload(app_main)
            self.assertIsNotNone(app_main.app)
            self.assertIsNone(vs.cv2)
        # Restore vision_service cleanly after test
        importlib.reload(vs)


class TestRecommendationQuality(unittest.TestCase):
    """
    Test suite for Section 4: Recommendation Quality & Consistency
    Covers: deduplication, determinism, dietary restrictions, missing data, empty candidate pool.
    """

    def setUp(self):
        # Set up a clean, isolated mock DataFrame for recommendation tests
        self.mock_dataset = pd.DataFrame([
            {
                "id": "rest_1",
                "name": "Phở Bò Gia Truyền",
                "tags": "phở bò nước dùng bắp bò truyền thống nóng",
                "rating": 4.8,
                "price": 65000,
                "lat": 10.7769,
                "lon": 106.7009,
                "address": "123 Lê Lợi, Quận 1",
                "district": "Quận 1"
            },
            {
                "id": "rest_2",
                "name": "Cơm Chay Thanh Lương",
                "tags": "cơm chay thanh đạm rau củ nấm đậu hũ",
                "rating": 4.6,
                "price": 40000,
                "lat": 10.7775,
                "lon": 106.7015,
                "address": "456 Nguyễn Huệ, Quận 1",
                "district": "Quận 1"
            },
            {
                "id": "rest_3",
                "name": "Lẩu Thái Cay Khun Thai",
                "tags": "lẩu thái cay sa tế hải sản tôm mực",
                "rating": 4.5,
                "price": 180000,
                "lat": 10.7780,
                "lon": 106.7020,
                "address": "789 Đồng Khởi, Quận 1",
                "district": "Quận 1"
            },
            {
                "id": "rest_4_dup",
                "name": "Phở Bò Gia Truyền",  # Duplicate name & address of rest_1
                "tags": "phở bò nước dùng",
                "rating": 4.2,
                "price": 65000,
                "lat": 10.7769,
                "lon": 106.7009,
                "address": "123 Lê Lợi, Quận 1",
                "district": "Quận 1"
            }
        ])

    @patch('app.core.recommender.get_dataset')
    @patch('app.core.recommender.get_vectorizer')
    def test_deduplication_filters_duplicate_restaurants(self, mock_get_vec, mock_get_df):
        """Verify that duplicate restaurants with same name and address are deduplicated."""
        mock_get_df.return_value = self.mock_dataset
        mock_vec = MagicMock()
        mock_vec.transform.side_effect = lambda texts: np.ones((len(texts), 4))
        mock_get_vec.return_value = mock_vec

        req = RecommendRequest(query="phở bò")
        res = recommend_restaurants(req)
        scores = res.get("scores", [])

        # Check that no duplicate IDs exist
        ids = [item['id'] for item in scores]
        self.assertEqual(len(ids), len(set(ids)))
        # Verify rest_4_dup was deduplicated against rest_1
        self.assertIn("rest_1", ids)
        self.assertNotIn("rest_4_dup", ids)

    @patch('app.core.recommender.get_dataset')
    def test_deterministic_ranking_results(self, mock_get_df):
        """Verify that running recommendation twice with identical inputs yields deterministic outputs."""
        mock_get_df.return_value = self.mock_dataset

        req = HybridRecommendRequest(
            user_gps=[10.7769, 106.7009],
            taste_vector=[0.2, 0.2, 0.2, 0.2, 0.4, 0.1],
            limit=5
        )

        res_1 = recommend_hybrid(req)
        res_2 = recommend_hybrid(req)

        ids_1 = [it.id for it in res_1.items]
        ids_2 = [it.id for it in res_2.items]
        self.assertEqual(ids_1, ids_2, "Recommendation ranking must be deterministic")

        scores_1 = [it.score for it in res_1.items]
        scores_2 = [it.score for it in res_2.items]
        self.assertEqual(scores_1, scores_2, "Composite scores must be identical")

    @patch('app.core.recommender.get_dataset')
    def test_strict_dietary_restrictions_vegetarian(self, mock_get_df):
        """Verify that vegetarian request returns only vegetarian candidates and no meat dishes."""
        df_with_meat_mushroom = pd.concat([
            self.mock_dataset,
            pd.DataFrame([{
                "id": "rest_meat_mushroom",
                "name": "Lẩu Gà Nấm",
                "tags": "lẩu gà nấm rau củ",
                "rating": 4.9,
                "price": 200000,
                "lat": 10.7770,
                "lon": 106.7010,
                "address": "99 Hai Bà Trưng, Quận 1",
                "district": "Quận 1"
            }])
        ], ignore_index=True)
        mock_get_df.return_value = df_with_meat_mushroom

        req = HybridRecommendRequest(
            dietary_exclusions=["chay"],
            user_gps=[10.7769, 106.7009],
            limit=5
        )

        res = recommend_hybrid(req)
        self.assertEqual(len(res.items), 1)
        for item in res.items:
            self.assertIn("chay", item.tags.lower(), f"Item {item.name} must be vegetarian")
            self.assertNotIn("gà", item.tags.lower())
            self.assertNotIn("lẩu thái", item.tags.lower())

    @patch('app.core.recommender.get_dataset')
    @patch('app.core.recommender.get_vectorizer')
    def test_empty_dataset_handling(self, mock_get_vec, mock_get_df):
        """Verify empty dataset returns valid empty responses for both recommend and recommend_hybrid."""
        empty_df = pd.DataFrame(columns=['id', 'name', 'tags', 'rating', 'price', 'lat', 'lon', 'district', 'address'])
        mock_get_df.return_value = empty_df
        mock_get_vec.return_value = MagicMock()

        res_rec = recommend_restaurants(RecommendRequest(query="phở"))
        self.assertEqual(res_rec["scores"], [])

        res_hyb = recommend_hybrid(HybridRecommendRequest(user_gps=[10.7769, 106.7009]))
        self.assertIsInstance(res_hyb, HybridRecommendResponse)
        self.assertEqual(res_hyb.total, 0)
        self.assertEqual(res_hyb.items, [])

    @patch('app.core.recommender.get_dataset')
    def test_empty_candidate_pool_handling(self, mock_get_df):
        """Verify that when no candidates match strict constraints, empty list is safely returned."""
        mock_get_df.return_value = self.mock_dataset

        # Extremely low price that matches nothing
        req = HybridRecommendRequest(
            max_price=1000,
            limit=5
        )

        res = recommend_hybrid(req)
        self.assertIsInstance(res, HybridRecommendResponse)
        self.assertEqual(res.total, 0)
        self.assertEqual(len(res.items), 0)

    @patch('app.core.recommender.get_dataset')
    def test_missing_data_resilience(self, mock_get_df):
        """Verify that NaN or missing fields in dataset do not cause crashes during recommendation."""
        df_with_nans = pd.DataFrame([
            {
                "id": "nan_rest_1",
                "name": "Quán Cơm Bình Dân",
                "tags": "cơm sườn chả",
                "rating": np.nan,  # Missing rating
                "price": np.nan,   # Missing price
                "lat": np.nan,     # Missing lat
                "lon": np.nan,     # Missing lon
                "address": None,
                "district": None
            }
        ])
        mock_get_df.return_value = df_with_nans

        req = HybridRecommendRequest(user_gps=[10.7769, 106.7009], max_price=100000, limit=5)
        res = recommend_hybrid(req)
        self.assertEqual(len(res.items), 1)
        item = res.items[0]
        self.assertFalse(math.isnan(item.score))
        self.assertFalse(math.isnan(item.distance_km))
        self.assertEqual(item.distance_km, 999.0)
        self.assertGreaterEqual(item.price, 0)

if __name__ == '__main__':
    unittest.main()
