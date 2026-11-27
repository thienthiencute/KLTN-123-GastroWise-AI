"""
Pre-M7.1 Baseline Recommender Reconstruction (commit a17ccc3).

Reconstructs the exact pre-M7.1 hybrid recommendation behavior for controlled
A/B offline benchmarking on identical datasets and user profiles:
1. Naive rating scale handling (only divides > 5.0 by 2; <= 5.0 Foody ratings stay unscaled).
2. Non-strict dietary filtering:
   - Vegetarian regex included 'nấm|rau củ' (matching meat+mushroom dishes like 'lẩu gà nấm').
   - Used `if mask.any():` fallback that silently dropped dietary filter when 0 matches existed.
3. No candidate-level (name, address) deduplication before top-K truncation.
4. No rating quality bonus in composite score and no deterministic multi-key tie-breaker.
"""

import math
import numpy as np
import pandas as pd
from app.core.text_utils import calculate_distance
from app.core.collaborative_filter import CollaborativeFilteringEngine
from app.core.recommender import (
    compute_restaurant_flavor_vector,
    compute_vector_cosine,
    compute_env_context,
)
from app.schemas.recommendation import (
    HybridRecommendRequest,
    HybridRecommendResponse,
    HybridRecommendItem,
)


def recommend_hybrid_baseline(
    request: HybridRecommendRequest,
    dataset_df: pd.DataFrame,
    cf_engine: CollaborativeFilteringEngine,
) -> HybridRecommendResponse:
    """Run the pre-M7.1 baseline hybrid recommendation logic."""
    if dataset_df is None or dataset_df.empty:
        return HybridRecommendResponse(
            total=0,
            is_cold_start=True,
            applied_weights={"w1_taste": 0.65, "w2_cf": 0.0, "w3_env": 0.35},
            items=[],
        )

    current_df = dataset_df.copy()
    user_id = request.user_id or ""
    user_gps = request.user_gps
    dietary_exclusions = request.dietary_exclusions or []
    taste_vector = (
        np.array(request.taste_vector, dtype=np.float32)
        if (request.taste_vector and len(request.taste_vector) == 6)
        else None
    )

    is_cold_start = cf_engine.is_user_cold_start(user_id) or not cf_engine.is_trained
    if is_cold_start:
        w1_taste, w2_cf, w3_env = 0.65, 0.0, 0.35
    else:
        w1_taste, w2_cf, w3_env = 0.45, 0.30, 0.25

    if user_gps and len(user_gps) == 2:
        current_df["distance_km"] = current_df.apply(
            lambda row: calculate_distance(user_gps[0], user_gps[1], row["lat"], row["lon"]),
            axis=1,
        )
    else:
        current_df["distance_km"] = 1.0

    # Pre-M7.1 non-strict dietary filtering with silent fallback
    for exclusion in dietary_exclusions:
        ex_clean = exclusion.strip().lower()
        if "chay" in ex_clean or "vegetarian" in ex_clean or "vegan" in ex_clean:
            chay_mask = current_df["tags"].str.contains(
                "chay|vegan|vegetarian|nấm|rau củ", case=False, na=False
            )
            if chay_mask.any():
                current_df = current_df[chay_mask]
        elif "không cay" in ex_clean:
            non_spicy_mask = ~current_df["tags"].str.contains(
                "cay|sa tế|mì cay|ớt", case=False, na=False
            )
            if non_spicy_mask.any():
                current_df = current_df[non_spicy_mask]
        elif "halal" in ex_clean:
            halal_mask = current_df["tags"].str.contains(
                "halal|muslim", case=False, na=False
            )
            if halal_mask.any():
                current_df = current_df[halal_mask]

    if request.max_price and request.max_price > 0:
        current_df = current_df[current_df["price"] <= request.max_price]

    if user_gps and len(user_gps) == 2:
        nearby_df = current_df[current_df["distance_km"] <= 20.0]
        if len(nearby_df) >= 10:
            current_df = nearby_df

    if current_df.empty:
        return HybridRecommendResponse(
            total=0,
            is_cold_start=is_cold_start,
            applied_weights={"w1_taste": w1_taste, "w2_cf": w2_cf, "w3_env": w3_env},
            items=[],
        )

    taste_scores = []
    cf_scores = []
    env_scores = []
    composite_scores = []
    all_reasons = []

    for row in current_df.itertuples():
        r_id = str(row.id)
        r_tags = str(row.tags)
        r_name = str(row.name)
        dist = float(getattr(row, "distance_km", 1.0))

        if taste_vector is not None:
            r_vector = compute_restaurant_flavor_vector(r_tags, r_name)
            s_taste = compute_vector_cosine(taste_vector, r_vector)
        else:
            s_taste = 0.50

        r_cf = cf_engine.predict_score(user_id, r_id) if not is_cold_start else 0.0
        s_env, _ = compute_env_context(r_tags, request.weather_type, request.temperature)

        lambda_dist = 0.12
        dist_penalty = lambda_dist * math.log(1.0 + max(0.0, dist))

        # Pre-M7.1 baseline had no rating quality bonus
        s_composite = (w1_taste * s_taste) + (w2_cf * r_cf) + (w3_env * s_env) - dist_penalty

        taste_scores.append(round(s_taste, 3))
        cf_scores.append(round(r_cf, 3))
        env_scores.append(round(s_env, 2))
        composite_scores.append(round(s_composite, 4))
        all_reasons.append(["Baseline recommendation"])

    current_df = current_df.copy()
    current_df["s_composite"] = composite_scores
    current_df["s_taste"] = taste_scores
    current_df["r_cf"] = cf_scores
    current_df["s_env"] = env_scores
    current_df["match_reasons"] = all_reasons

    # Pre-M7.1 sorted only on s_composite without tie-breaking or (name, address) dedup
    sorted_df = current_df.sort_values(by=["s_composite"], ascending=[False])
    limit = request.limit or 10
    top_candidates = sorted_df.head(limit)

    output_items = []
    seen_ids = set()
    for row in top_candidates.itertuples():
        r_id = str(row.id)
        if r_id in seen_ids:
            continue
        seen_ids.add(r_id)
        raw_p = getattr(row, "price", 50000)
        clean_p = 50000 if (raw_p is None or pd.isna(raw_p)) else int(raw_p)
        output_items.append(
            HybridRecommendItem(
                id=r_id,
                name=str(row.name),
                tags=str(row.tags),
                score=float(getattr(row, "s_composite", 0.0)),
                taste_score=float(getattr(row, "s_taste", 0.0)),
                cf_score=float(getattr(row, "r_cf", 0.0)),
                env_score=float(getattr(row, "s_env", 1.0)),
                distance_km=round(float(getattr(row, "distance_km", 1.0)), 2),
                price=clean_p,
                match_reasons=getattr(row, "match_reasons", []),
                explanation="Baseline recommendation",
            )
        )

    return HybridRecommendResponse(
        total=len(output_items),
        is_cold_start=is_cold_start,
        applied_weights={
            "w1_taste": w1_taste,
            "w2_cf": w2_cf,
            "w3_env": w3_env,
            "lambda_dist": 0.12,
        },
        items=output_items,
    )
