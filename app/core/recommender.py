import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from app.config import (
    TAG_KNOWLEDGE_BASE, LOCATION_NAMES, MAJOR_CITIES, 
    CANDIDATE_TAGS, PRIORITY_TAGS, ADJECTIVE_TAGS
)
from app.core.text_utils import translate_query, calculate_distance
from app.db.mongo import get_dataset, get_vectorizer
from app.schemas.recommendation import RecommendRequest

def recommend_restaurants(request_data: RecommendRequest):
    df = get_dataset()
    vectorizer = get_vectorizer()
    
    if df is None or df.empty or vectorizer is None:
        return {"sort_by": "relevance", "scores": []}
        
    # 1. PRE-PROCESS QUERY
    original_query = request_data.query
    processed_query = translate_query(original_query)
    user_gps = request_data.user_gps
    
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
            filtered_df = filtered_df[filtered_df['distance_km'] <= 20.0]
            
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

    # STEP 4: TF-IDF COSINE SIMILARITY & BOOSTING
    final_query_text = " ".join(extracted_tags) if extracted_tags else processed_query
    
    try:
        qv = vectorizer.transform([final_query_text])
        tm = vectorizer.transform(filtered_df['tags'])
        base_scores = cosine_similarity(qv, tm).flatten()
    except Exception:
        base_scores = [0.0] * len(filtered_df)

    boosted_scores = []
    name_query = processed_query.lower().strip() 

    for idx, row in enumerate(filtered_df.itertuples()):
        score = base_scores[idx]
        row_name = str(row.name).lower()
        
        if target_dish_tags:
            for dish in target_dish_tags:
                if dish in row_name:
                    score += 0.3 

        if len(name_query) > 2:
            if name_query == row_name:
                score += 10.0
            elif name_query in row_name:
                score += 5.0
        
        boosted_scores.append(score)

    filtered_df = filtered_df.copy()
    filtered_df['S_taste'] = boosted_scores

    final_candidates = filtered_df

    # STEP 5: SORTING
    sort_by = "relevance"
    query_lower = processed_query.lower()
    
    if "gần" in query_lower:
        sort_by = "distance"
        final_candidates = final_candidates.sort_values('distance_km', ascending=True)
    elif "rẻ" in query_lower:
        sort_by = "price"
        final_candidates = final_candidates.sort_values('price', ascending=True)
    elif any(x in query_lower for x in ['ngon', 'tốt nhất', 'nổi tiếng', 'rating', 'đánh giá']):
        sort_by = "rating"
        final_candidates = final_candidates.sort_values('rating', ascending=False)
    else:
        final_candidates = final_candidates.sort_values('S_taste', ascending=False)
        
    scores_list = []
    for _, row in final_candidates.head(64).iterrows():
        scores_list.append({
            "id": str(row['id']),
            "name": str(row['name']),
            "tags": str(row['tags']),
            "S_taste": float(row.get('S_taste', 0.0)),
            "distance_km": float(row.get('distance_km', 999.0)),
            "price": int(row['price'])
        })
        
    return {"sort_by": sort_by, "scores": scores_list}
