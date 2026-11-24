import math
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Optional, Tuple, Dict, Any
from app.config import (
    TAG_KNOWLEDGE_BASE, LOCATION_NAMES, MAJOR_CITIES, 
    CANDIDATE_TAGS, PRIORITY_TAGS, ADJECTIVE_TAGS
)
from app.core.text_utils import translate_query, calculate_distance
from app.db.mongo import get_dataset, get_vectorizer
from app.core.collaborative_filter import cf_engine
from app.core.rating_normalizer import normalize_rating, RatingScale
from app.schemas.recommendation import (
    RecommendRequest, HybridRecommendRequest, 
    HybridRecommendResponse, HybridRecommendItem
)

# Từ khóa định danh 6 chiều vị Taste DNA
TASTE_KEYWORDS = {
    0: ['cay', 'sa tế', 'ớt', 'lẩu thái', 'mì cay', 'tiêu', 'nướng cay', 'sốt cay', 'wasabi'], # spicy
    1: ['ngọt', 'chè', 'trà sữa', 'bánh', 'kem', 'đường', 'sữa', 'mật ong', 'sinh tố', 'bingsu'], # sweet
    2: ['chua', 'canh chua', 'me', 'chanh', 'xoài', 'giấm', 'lẩu chua cay', 'sốt me', 'nem chua'], # sour
    3: ['mặn', 'rim', 'mắm', 'kho', 'đậm đà', 'muối', 'nước mắm', 'thịt kho'], # salty
    4: ['thịt', 'nướng', 'lẩu', 'nước dùng', 'hầm', 'tôm', 'cua', 'hải sản', 'bắp bò', 'phở', 'bò kho'], # umami
    5: ['đắng', 'khổ qua', 'cà phê', 'trà đen', 'matcha', 'socola đen', 'rau đắng'], # bitter
}

def compute_restaurant_flavor_vector(tags_str: str, name_str: str) -> np.ndarray:
    """
    [TASK-P2-01] Tính toán vector hương vị 6 chiều cho nhà hàng dựa trên tags và tên món:
    [spicy, sweet, sour, salty, umami, bitter] in [0.0, 1.0].
    """
    text = f"{str(name_str).lower()} {str(tags_str).lower()}"
    vector = np.array([0.2, 0.2, 0.2, 0.2, 0.3, 0.1], dtype=np.float32) # prior baseline

    for dim_idx, kw_list in TASTE_KEYWORDS.items():
        hits = sum(1 for kw in kw_list if kw in text)
        if hits > 0:
            vector[dim_idx] = min(1.0, vector[dim_idx] + hits * 0.25)

    return vector

def compute_vector_cosine(v1: np.ndarray, v2: np.ndarray) -> float:
    """Tính cosine similarity giữa 2 vector hương vị."""
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.5
    return float(np.dot(v1, v2) / (norm1 * norm2))

def compute_env_context(
    tags_str: str, 
    weather_type: Optional[str], 
    temperature: Optional[float]
) -> Tuple[float, Optional[str]]:
    """
    [TASK-P2-01] Đánh giá trọng số ngữ cảnh thời tiết S_env:
    - Trời mưa/mát: +30% cho món lẩu, nướng, súp nóng, phở, mì cay.
    - Trời nắng nóng (>= 31 độ): +30% cho món chè, trà sữa, kem, gỏi cuốn thanh mát.
    """
    tags_lower = str(tags_str).lower()
    w_type = (weather_type or '').lower()
    temp = temperature if temperature is not None else 28.0

    if w_type == 'rainy' or 'mưa' in w_type or temp <= 24.0:
        warm_keywords = ['lẩu', 'nướng', 'súp', 'cháo', 'phở', 'mì cay', 'nóng']
        if any(kw in tags_lower for kw in warm_keywords):
            return 1.30, "🌧️ Món nóng ấm lý tưởng cho ngày mưa mát mẻ"

    if w_type == 'hot' or 'nắng' in w_type or temp >= 31.0:
        refreshing_keywords = ['chè', 'kem', 'trà sữa', 'bingsu', 'gỏi', 'cuốn', 'thanh mát', 'giải nhiệt', 'nước ép']
        if any(kw in tags_lower for kw in refreshing_keywords):
            return 1.30, f"☀️ Thức uống & món ăn thanh mát giải nhiệt ({int(temp)}°C)"

    return 1.0, None

def generate_recommendation_explanation(
    taste_score: float, 
    distance_km: float, 
    dish_match: bool, 
    taste_vector: Optional[List[float]] = None
) -> str:
    reasons = []
    if dish_match:
        reasons.append("Đúng món bạn yêu cầu")
    if taste_vector and len(taste_vector) >= 6:
        spicy_val = taste_vector[0]
        if spicy_val >= 0.7 and taste_score >= 0.5:
            reasons.append("Hợp gu cay nồng của bạn")
    if distance_km <= 2.0:
        reasons.append(f"Gần bạn ({distance_km:.1f}km)")
    if taste_score >= 0.75:
        reasons.append("Hợp khẩu vị Taste DNA (>=80%)")
    
    if not reasons:
        reasons.append("Địa điểm ẩm thực nổi tiếng được đánh giá cao")
        
    return " • ".join(reasons)

def recommend_restaurants(request_data: RecommendRequest):
    df = get_dataset()
    vectorizer = get_vectorizer()
    
    if df is None or df.empty or vectorizer is None:
        return {"sort_by": "relevance", "scores": []}
        
    # 1. PRE-PROCESS QUERY
    original_query = request_data.query
    processed_query = translate_query(original_query)
    user_gps = request_data.user_gps
    taste_vector = request_data.taste_vector
    dietary_exclusions = request_data.dietary_exclusions or []
    
    current_df = df.copy()
    
    if user_gps and len(user_gps) == 2:
        current_df['distance_km'] = current_df.apply(
            lambda row: calculate_distance(user_gps[0], user_gps[1], row['lat'], row['lon']), 
            axis=1
        )
    else:
        current_df['distance_km'] = 999.0
        
    temp_query = " " + processed_query.lower() + " "
    
    for k, v in TAG_KNOWLEDGE_BASE.items():
        if f" {k} " in temp_query:
            temp_query = temp_query.replace(f" {k} ", f" {v} ")

    locations_to_filter = []
    for k, v in LOCATION_NAMES.items():
        if f" {k} " in temp_query:
            locations_to_filter.append(v)
            temp_query = temp_query.replace(f" {k} ", " ")
    
    extracted_tags = []
    sorted_candidates = sorted(CANDIDATE_TAGS, key=len, reverse=True)
    for tag in sorted_candidates:
        if f" {tag} " in temp_query:
            extracted_tags.append(tag)
            temp_query = temp_query.replace(f" {tag} ", " ")
            
    mandatory_tags = [t for t in extracted_tags if t in PRIORITY_TAGS]
    
    # STEP 1: FILTER BY LOCATION & GPS
    filtered_df = current_df
    
    # Dietary Exclusions Filter
    if dietary_exclusions:
        for exclusion in dietary_exclusions:
            ex_lower = exclusion.strip().lower()
            if 'chay' in ex_lower or 'vegetarian' in ex_lower or 'vegan' in ex_lower:
                filtered_df = filtered_df[filtered_df['tags'].str.contains('chay|vegan|vegetarian|nấm|rau củ', case=False, na=False)]
            elif 'không cay' in ex_lower:
                filtered_df = filtered_df[~filtered_df['tags'].str.contains('cay|sa tế|mì cay|ớt', case=False, na=False)]
            elif 'halal' in ex_lower:
                filtered_df = filtered_df[filtered_df['tags'].str.contains('halal|muslim', case=False, na=False)]
    
    if locations_to_filter:
        city_filters = [loc for loc in locations_to_filter if loc in MAJOR_CITIES]
        district_filters = [loc for loc in locations_to_filter if loc not in MAJOR_CITIES]

        if city_filters:
            pattern = '|'.join(city_filters)
            filtered_df = filtered_df[filtered_df['address'].str.contains(pattern, case=False, na=False)]

        if district_filters:
            filtered_df = filtered_df[filtered_df['district'].isin(district_filters)]

    elif request_data.city_filter:
        filtered_df = filtered_df[filtered_df['district'].str.contains(request_data.city_filter, case=False, na=False)]
    else:
        if user_gps and len(user_gps) == 2:
            filtered_df = filtered_df[filtered_df['distance_km'] <= 25.0]
            
    # STEP 2: FILTER BY MANDATORY TAGS (TIME OF DAY)
    if mandatory_tags:
        for tag in mandatory_tags:
            filtered_df = filtered_df[filtered_df['tags'].str.contains(tag, case=False, na=False)]
            
    if filtered_df.empty:
        return {"sort_by": "relevance", "scores": []}
        
    # STEP 3: FILTER BY FOOD DISH TAGS
    target_dish_tags = [t for t in extracted_tags if t not in ADJECTIVE_TAGS and t not in PRIORITY_TAGS]
    
    if target_dish_tags:
        matches = []
        for index, row in filtered_df.iterrows():
            row_tags = str(row['tags']).lower()
            if any(dish in row_tags for dish in target_dish_tags):
                matches.append(index)
        
        if len(matches) > 0:
            filtered_df = filtered_df.loc[matches]

    # STEP 4: TF-IDF COSINE SIMILARITY & TASTE DNA BOOSTING
    final_query_text = " ".join(extracted_tags) if extracted_tags else processed_query
    
    try:
        qv = vectorizer.transform([final_query_text])
        tm = vectorizer.transform(filtered_df['tags'])
        base_scores = cosine_similarity(qv, tm).flatten()
    except Exception:
        base_scores = [0.0] * len(filtered_df)

    boosted_scores = []
    dish_match_flags = []
    name_query = processed_query.lower().strip() 

    spicy_weight = taste_vector[0] if (taste_vector and len(taste_vector) >= 6) else 0.5
    sweet_weight = taste_vector[1] if (taste_vector and len(taste_vector) >= 6) else 0.5

    for idx, row in enumerate(filtered_df.itertuples()):
        score = base_scores[idx]
        row_name = str(row.name).lower()
        row_tags = str(row.tags).lower()
        has_dish_match = False
        
        if target_dish_tags:
            for dish in target_dish_tags:
                if dish in row_name or dish in row_tags:
                    score += 0.35
                    has_dish_match = True

        if len(name_query) > 2:
            if name_query == row_name:
                score += 10.0
                has_dish_match = True
            elif name_query in row_name:
                score += 5.0
                has_dish_match = True

        if spicy_weight >= 0.7 and any(w in row_tags for w in ['cay', 'lẩu', 'nướng', 'nước lèo']):
            score += 0.25
        if sweet_weight >= 0.7 and any(w in row_tags for w in ['chè', 'trà sữa', 'ngọt', 'bánh']):
            score += 0.25

        boosted_scores.append(score)
        dish_match_flags.append(has_dish_match)

    filtered_df = filtered_df.copy()
    filtered_df['S_taste'] = boosted_scores
    filtered_df['dish_match'] = dish_match_flags

    final_candidates = filtered_df

    # Deduplicate candidates by id and by name & address
    final_candidates = final_candidates.drop_duplicates(subset=['id'], keep='first')
    if 'address' in final_candidates.columns:
        final_candidates = final_candidates.drop_duplicates(subset=['name', 'address'], keep='first')

    # Normalize rating safely
    if 'rating' in final_candidates.columns:
        final_candidates['rating'] = final_candidates['rating'].apply(lambda x: normalize_rating(x, default=3.0))
    else:
        final_candidates['rating'] = 3.0

    final_candidates['distance_km'] = pd.to_numeric(final_candidates['distance_km'], errors='coerce').fillna(999.0)
    final_candidates['price'] = pd.to_numeric(final_candidates['price'], errors='coerce').fillna(50000).astype(int)

    # STEP 5: SORTING (Deterministic with secondary & tie-breaker keys)
    sort_by = "relevance"
    query_lower = processed_query.lower()
    
    if "gần" in query_lower:
        sort_by = "distance"
        final_candidates = final_candidates.sort_values(
            by=['distance_km', 'S_taste', 'rating', 'id'],
            ascending=[True, False, False, True]
        )
    elif "rẻ" in query_lower:
        sort_by = "price"
        final_candidates = final_candidates.sort_values(
            by=['price', 'S_taste', 'rating', 'id'],
            ascending=[True, False, False, True]
        )
    elif any(x in query_lower for x in ['ngon', 'tốt nhất', 'nổi tiếng', 'rating', 'đánh giá']):
        sort_by = "rating"
        final_candidates = final_candidates.sort_values(
            by=['rating', 'S_taste', 'distance_km', 'id'],
            ascending=[False, False, True, True]
        )
    else:
        final_candidates = final_candidates.sort_values(
            by=['S_taste', 'rating', 'distance_km', 'id'],
            ascending=[False, False, True, True]
        )
        
    scores_list = []
    for _, row in final_candidates.head(64).iterrows():
        dist = float(row.get('distance_km', 999.0))
        taste_sc = float(row.get('S_taste', 0.0))
        d_match = bool(row.get('dish_match', False))
        raw_p = row.get('price', 50000)
        clean_p = 50000 if (raw_p is None or pd.isna(raw_p)) else int(raw_p)
        
        explanation = generate_recommendation_explanation(
            taste_score=taste_sc,
            distance_km=dist,
            dish_match=d_match,
            taste_vector=taste_vector
        )

        scores_list.append({
            "id": str(row['id']),
            "name": str(row['name']),
            "tags": str(row['tags']),
            "S_taste": round(taste_sc, 3),
            "distance_km": round(dist, 2),
            "price": clean_p,
            "explanation": explanation
        })
        
    return {"sort_by": sort_by, "scores": scores_list}

# ==============================================================================
# [TASK-P2-01 & TASK-P2-02] 4-STAGE HYBRID AI RECOMMENDATION PIPELINE
# ==============================================================================

def recommend_hybrid(request: HybridRecommendRequest) -> HybridRecommendResponse:
    """
    4-Stage Industrial Hybrid Recommendation Engine:
    Stage 1: Hard Filtering (Geo radius, Dietary Constraints, Price Cap)
    Stage 2: Content-Based Taste DNA Cosine Similarity
    Stage 3: SVD Collaborative Filtering (Matrix Factorization)
    Stage 4: Contextual Weather Boosting & Distance Decay Ranking
    """
    df = get_dataset()
    if df is None or df.empty:
        return HybridRecommendResponse(
            total=0,
            is_cold_start=True,
            applied_weights={"w1_taste": 0.65, "w2_cf": 0.0, "w3_env": 0.35},
            items=[]
        )

    current_df = df.copy()
    user_id = request.user_id or ""
    user_gps = request.user_gps
    dietary_exclusions = request.dietary_exclusions or []
    taste_vector = np.array(request.taste_vector, dtype=np.float32) if (request.taste_vector and len(request.taste_vector) == 6) else None
    
    # Check Cold-Start
    is_cold_start = cf_engine.is_user_cold_start(user_id) or not cf_engine.is_trained
    if is_cold_start:
        w1_taste = 0.65
        w2_cf = 0.0
        w3_env = 0.35
    else:
        w1_taste = 0.45
        w2_cf = 0.30
        w3_env = 0.25

    # -------------------------------------------------------------------------
    # STAGE 1: CANDIDATE RETRIEVAL & HARD CONSTRAINTS
    # -------------------------------------------------------------------------
    if user_gps and len(user_gps) == 2:
        current_df['distance_km'] = current_df.apply(
            lambda row: calculate_distance(user_gps[0], user_gps[1], row['lat'], row['lon']),
            axis=1
        )
    else:
        current_df['distance_km'] = 1.0 # fallback default

    # Deduplicate candidate base by id and (name, address)
    current_df = current_df.drop_duplicates(subset=['id'], keep='first')
    if 'address' in current_df.columns:
        current_df = current_df.drop_duplicates(subset=['name', 'address'], keep='first')

    # 1.1 Dietary Constraint Exclusions (Strict filtering)
    for exclusion in dietary_exclusions:
        ex_clean = exclusion.strip().lower()
        if 'chay' in ex_clean or 'vegetarian' in ex_clean or 'vegan' in ex_clean:
            current_df = current_df[current_df['tags'].str.contains('chay|vegan|vegetarian|nấm|rau củ', case=False, na=False)]
        elif 'không cay' in ex_clean:
            current_df = current_df[~current_df['tags'].str.contains('cay|sa tế|mì cay|ớt', case=False, na=False)]
        elif 'halal' in ex_clean:
            current_df = current_df[current_df['tags'].str.contains('halal|muslim', case=False, na=False)]

    # 1.2 Price Cap Filter
    if request.max_price and request.max_price > 0:
        current_df = current_df[current_df['price'] <= request.max_price]

    # 1.3 Proximity Candidate Pool (Filter to 15km if GPS exists, or top by rating)
    if user_gps and len(user_gps) == 2:
        nearby_df = current_df[current_df['distance_km'] <= 20.0]
        if len(nearby_df) >= 10:
            current_df = nearby_df

    if current_df.empty:
        return HybridRecommendResponse(
            total=0,
            is_cold_start=is_cold_start,
            applied_weights={"w1_taste": w1_taste, "w2_cf": w2_cf, "w3_env": w3_env},
            items=[]
        )

    # -------------------------------------------------------------------------
    # STAGE 2 & 3: TASTE DNA MATCHING & SVD COLLABORATIVE FILTERING
    # -------------------------------------------------------------------------
    taste_scores = []
    cf_scores = []
    env_scores = []
    env_reasons = []
    composite_scores = []
    all_reasons = []

    for row in current_df.itertuples():
        r_id = str(row.id)
        r_tags = str(row.tags)
        r_name = str(row.name)
        dist = float(getattr(row, 'distance_km', 1.0))
        rating = normalize_rating(getattr(row, 'rating', None), default=3.5)

        # 2.1 Taste DNA Cosine Similarity
        if taste_vector is not None:
            r_vector = compute_restaurant_flavor_vector(r_tags, r_name)
            s_taste = compute_vector_cosine(taste_vector, r_vector)
        else:
            s_taste = 0.50 # Neutral prior

        # 2.2 SVD Collaborative Filtering
        if not is_cold_start:
            r_cf = cf_engine.predict_score(user_id, r_id)
        else:
            r_cf = 0.0

        # 2.3 Contextual Weather & Environmental Boost
        s_env, env_reason = compute_env_context(r_tags, request.weather_type, request.temperature)

        # 2.4 Distance Decay Penalty: lambda_dist * ln(1 + D)
        lambda_dist = 0.12
        dist_penalty = lambda_dist * math.log(1.0 + max(0.0, dist))

        # Final Composite Score Formula with Rating Quality Factor
        rating_bonus = 0.05 * (rating / 5.0)
        s_composite = (w1_taste * s_taste) + (w2_cf * r_cf) + (w3_env * s_env) + rating_bonus - dist_penalty

        # Explanation Justification Synthesis
        reasons_list = []
        if s_taste >= 0.70:
            reasons_list.append(f"✨ Hợp khẩu vị Taste DNA ({int(s_taste * 100)}%)")
        if taste_vector is not None and taste_vector[0] >= 0.7 and any(w in r_tags.lower() for w in ['cay', 'sa tế', 'lẩu thái']):
            reasons_list.append("🌶️ Chuẩn gu cay nồng")
        if taste_vector is not None and taste_vector[1] >= 0.7 and any(w in r_tags.lower() for w in ['chè', 'ngọt', 'trà sữa']):
            reasons_list.append("🍰 Hợp gu hảo ngọt")
        if env_reason:
            reasons_list.append(env_reason)
        if dist <= 2.0:
            reasons_list.append(f"📍 Gần bạn ({dist:.1f}km)")
        if not is_cold_start and r_cf >= 0.60:
            reasons_list.append("👥 Được thực khách cùng sở thích yêu thích")
        if rating >= 4.7:
            reasons_list.append(f"⭐ Đánh giá xuất sắc ({rating:.1f}★)")

        if not reasons_list:
            reasons_list.append("🌟 Quán ngon nổi tiếng được yêu thích trên GastroWise")

        taste_scores.append(round(s_taste, 3))
        cf_scores.append(round(r_cf, 3))
        env_scores.append(round(s_env, 2))
        composite_scores.append(round(s_composite, 4))
        all_reasons.append(reasons_list)

    current_df = current_df.copy()
    current_df['s_composite'] = composite_scores
    current_df['s_taste'] = taste_scores
    current_df['r_cf'] = cf_scores
    current_df['s_env'] = env_scores
    current_df['match_reasons'] = all_reasons

    # -------------------------------------------------------------------------
    # STAGE 4: RANKING, EXPLAINABILITY & DEDUPLICATION (Deterministic)
    # -------------------------------------------------------------------------
    if 'rating' not in current_df.columns:
        current_df['rating'] = 3.5
    else:
        current_df['rating'] = current_df['rating'].apply(lambda x: normalize_rating(x, default=3.5))

    sorted_df = current_df.sort_values(
        by=['s_composite', 's_taste', 'rating', 'id'],
        ascending=[False, False, False, True]
    )
    limit = request.limit or 10
    top_candidates = sorted_df.head(limit)

    output_items: List[HybridRecommendItem] = []
    seen_ids = set()
    for row in top_candidates.itertuples():
        r_id = str(row.id)
        if r_id in seen_ids:
            continue
        seen_ids.add(r_id)

        reasons = getattr(row, 'match_reasons', [])
        explanation_str = " • ".join(reasons[:2]) if reasons else "Gợi ý nổi bật"
        raw_p = getattr(row, 'price', 50000)
        clean_p = 50000 if (raw_p is None or pd.isna(raw_p)) else int(raw_p)

        output_items.append(
            HybridRecommendItem(
                id=str(row.id),
                name=str(row.name),
                tags=str(row.tags),
                score=float(getattr(row, 's_composite', 0.0)),
                taste_score=float(getattr(row, 's_taste', 0.0)),
                cf_score=float(getattr(row, 'r_cf', 0.0)),
                env_score=float(getattr(row, 's_env', 1.0)),
                distance_km=round(float(getattr(row, 'distance_km', 1.0)), 2),
                price=clean_p,
                match_reasons=reasons,
                explanation=explanation_str
            )
        )

    return HybridRecommendResponse(
        total=len(output_items),
        is_cold_start=is_cold_start,
        applied_weights={
            "w1_taste": w1_taste,
            "w2_cf": w2_cf,
            "w3_env": w3_env,
            "lambda_dist": 0.12
        },
        items=output_items
    )
