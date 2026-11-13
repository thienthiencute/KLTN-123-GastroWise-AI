"""
Unit Test cho TASK-P2-01 & TASK-P2-02:
Hybrid AI Recommendation Engine & TruncatedSVD Collaborative Filtering
"""
import numpy as np
import pandas as pd
from app.core.collaborative_filter import CollaborativeFilteringEngine, EVENT_WEIGHTS
from app.core.recommender import (
    compute_restaurant_flavor_vector,
    compute_vector_cosine,
    compute_env_context,
    recommend_hybrid
)
from app.schemas.recommendation import HybridRecommendRequest

def test_flavor_vector_extraction():
    # Quán lẩu thái cay nồng
    vec = compute_restaurant_flavor_vector("lẩu thái sa tế hải sản ớt cay", "Lẩu Thái Khun Thai")
    assert vec[0] > 0.4, f"Spicy score should be elevated, got {vec[0]}"
    assert vec[4] > 0.4, f"Umami score should be elevated, got {vec[4]}"

    # Quán chè trà sữa ngọt
    vec_sweet = compute_restaurant_flavor_vector("chè thái sầu riêng trà sữa trân châu đường đen", "Tiệm Chè Bưởi")
    assert vec_sweet[1] > 0.4, f"Sweet score should be elevated, got {vec_sweet[1]}"

def test_cosine_similarity():
    v1 = np.array([0.9, 0.2, 0.3, 0.4, 0.8, 0.1]) # Gu cay & umami
    v2 = np.array([0.8, 0.1, 0.2, 0.5, 0.7, 0.1]) # Quán lẩu cay
    v3 = np.array([0.1, 0.9, 0.1, 0.1, 0.2, 0.1]) # Tiệm chè

    sim_high = compute_vector_cosine(v1, v2)
    sim_low = compute_vector_cosine(v1, v3)

    assert sim_high > sim_low, f"Matching tastes should have higher cosine similarity: {sim_high} vs {sim_low}"

def test_collaborative_filtering_engine():
    engine = CollaborativeFilteringEngine(n_factors=2)
    assert engine.is_user_cold_start("new_user_123") is True

    # Giả lập interactions giữa 3 users và 3 restaurants
    interactions = [
        {"userId": "user_1", "targetId": "rest_A", "eventType": "REVIEW", "rating": 5.0},
        {"userId": "user_1", "targetId": "rest_B", "eventType": "CLICK"},
        {"userId": "user_2", "targetId": "rest_A", "eventType": "REVIEW", "rating": 4.5},
        {"userId": "user_2", "targetId": "rest_C", "eventType": "SAVE"},
        {"userId": "user_3", "targetId": "rest_B", "eventType": "REVIEW", "rating": 5.0},
        {"userId": "user_3", "targetId": "rest_C", "eventType": "CLICK"},
    ]

    success = engine.train_from_interactions(interactions)
    assert success is True
    assert engine.is_trained is True
    assert engine.is_user_cold_start("user_1") is False

    score = engine.predict_score("user_1", "rest_A")
    assert 0.0 <= score <= 1.0, f"Predicted score {score} out of bounds"

def test_environmental_context_boosting():
    # Trời mưa mát
    env_score, reason = compute_env_context("lẩu thái hải sản, bò nướng sốt cay", "rainy", 22.0)
    assert env_score >= 1.25
    assert reason is not None and "mưa" in reason

    # Trời nắng nóng
    env_score_hot, reason_hot = compute_env_context("trà sữa trân châu, chè bưởi, kem tuyết", "hot", 34.0)
    assert env_score_hot >= 1.25
    assert reason_hot is not None and "thanh mát" in reason_hot

def test_hybrid_recommender_pipeline():
    # Tạo mock DataFrame vào mongo dataset cache
    import app.db.mongo as mongo_mod
    mock_df = pd.DataFrame([
        {
            "id": "mock_rest_1",
            "name": "Lẩu Cay Tứ Xuyên",
            "tags": "lẩu thái cay sa tế hải sản",
            "rating": 4.8,
            "price": 150000,
            "lat": 10.7769,
            "lon": 106.7009,
            "address": "Quận 1, TP. HCM",
            "district": "Quận 1"
        },
        {
            "id": "mock_rest_2",
            "name": "Cơm Chay Thanh Tâm",
            "tags": "cơm chay thanh đạm rau củ nấm",
            "rating": 4.6,
            "price": 45000,
            "lat": 10.7770,
            "lon": 106.7010,
            "address": "Quận 1, TP. HCM",
            "district": "Quận 1"
        },
        {
            "id": "mock_rest_3",
            "name": "Tiệm Trà & Chè Sài Gòn",
            "tags": "chè thái sầu riêng trà sữa kem",
            "rating": 4.7,
            "price": 35000,
            "lat": 10.7780,
            "lon": 106.7020,
            "address": "Quận 1, TP. HCM",
            "district": "Quận 1"
        }
    ])
    mongo_mod.df = mock_df

    # Case A: User thích ăn cay
    req_spicy = HybridRecommendRequest(
        user_id="user_spicy",
        user_gps=[10.7769, 106.7009],
        taste_vector=[0.9, 0.2, 0.1, 0.4, 0.8, 0.1], # spicy 0.9
        weather_type="rainy",
        temperature=23.0,
        limit=5
    )
    res_spicy = recommend_hybrid(req_spicy)
    assert res_spicy.total > 0
    # Top 1 phải là quán lẩu cay
    top_item = res_spicy.items[0]
    assert "Lẩu" in top_item.name or "cay" in top_item.tags
    assert len(top_item.match_reasons) > 0
    assert top_item.explanation is not None

    # Case B: Ăn chay
    req_chay = HybridRecommendRequest(
        user_id="user_chay",
        user_gps=[10.7769, 106.7009],
        dietary_exclusions=["chay"],
        limit=5
    )
    res_chay = recommend_hybrid(req_chay)
    for it in res_chay.items:
        assert "chay" in it.tags.lower()

    print("-> Tất cả unit tests cho Hybrid Recommendation Engine ĐÃ PASS THÀNH CÔNG!")

if __name__ == "__main__":
    test_flavor_vector_extraction()
    test_cosine_similarity()
    test_collaborative_filtering_engine()
    test_environmental_context_boosting()
    test_hybrid_recommender_pipeline()

