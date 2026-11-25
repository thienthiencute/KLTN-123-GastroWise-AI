"""
Synthetic Evaluation Dataset for GastroWise AI Recommender (M7.2).

IMPORTANT DISCLAIMER:
Real historical production user interaction logs are not available in this
offline repository environment. All restaurant records, user profiles,
interaction histories, and graded relevance labels in this module are
clearly labeled SYNTHETIC EVALUATION FIXTURES designed to test ranking,
dietary constraints, rating normalization, deduplication, and cold-start
behavior reproducibly.
"""

from typing import Dict, List, Any
import pandas as pd
from app.core.rating_normalizer import detect_restaurant_rating_scale, normalize_rating

DATASET_METADATA = {
    "name": "gastrowise_synthetic_benchmark_v1",
    "is_synthetic": True,
    "seed": 42,
    "description": (
        "Synthetic multi-profile benchmark simulating Foody 10-point crawled "
        "restaurants, GastroWise 5-star user-reviewed restaurants, duplicate "
        "records, dietary constraints, budget tiers, and HCMC GPS coordinates."
    ),
    "limitations": [
        "Synthetic ground-truth relevance grades reflect domain-rule expectations, not real user clicks/orders.",
        "Catalog size (24 raw rows, 22 unique restaurants) is smaller than production MongoDB Atlas.",
        "Collaborative filtering interactions are synthetic fixtures for cold-start vs warm-start verification.",
    ],
}


def get_raw_synthetic_restaurants() -> List[Dict[str, Any]]:
    """
    Return raw restaurant documents mimicking MongoDB documents before normalization.
    Includes:
    - Foody 10-point documents (with diemChatLuong/diemViTri and reviewsCount=0),
      including low Foody ratings <= 5.0 (e.g. 3.6/10 -> 1.8/5, 4.0/10 -> 2.0/5)
      and high Foody ratings (e.g. 9.2/10 -> 4.6/5).
    - GastroWise 5-star documents (reviewsCount > 0).
    - Duplicate restaurant records with distinct IDs but identical (name, address).
    """
    return [
        # --- Spicy & Hotpot (Lẩu / Mì cay / Nướng) ---
        {
            "id": "r_spicy_1",
            "name": "Lẩu Thái Khun Thai",
            "tags": "lẩu thái cay sa tế ớt hải sản tôm mực nóng",
            "diemTrungBinh": 9.0,
            "diemChatLuong": 9.1,
            "reviewsCount": 0,
            "price": 180000,
            "lat": 10.7769,
            "lon": 106.7009,
            "address": "123 Lê Lợi, Quận 1",
            "district": "Quận 1",
        },
        {
            "id": "r_spicy_2",
            "name": "Mì Cay Seoul Quận 1",
            "tags": "mì cay ớt sa tế nước dùng nóng thịt bò",
            "diemTrungBinh": 4.6,
            "reviewsCount": 24,
            "price": 65000,
            "lat": 10.7782,
            "lon": 106.7025,
            "address": "45 Pasteur, Quận 1",
            "district": "Quận 1",
        },
        {
            "id": "r_spicy_3_poor_foody",
            "name": "Lẩu Cay Giá Rẻ Bình Thạnh",
            "tags": "lẩu thái cay ớt sa tế",
            "diemTrungBinh": 3.8,  # 3.8/10 Foody -> 1.9/5 (poor quality)
            "diemChatLuong": 3.6,
            "reviewsCount": 0,
            "price": 90000,
            "lat": 10.8012,
            "lon": 106.7145,
            "address": "88 Xô Viết Nghệ Tĩnh, Bình Thạnh",
            "district": "Bình Thạnh",
        },
        {
            "id": "r_spicy_4_dup",
            "name": "Lẩu Thái Khun Thai",  # Duplicate of r_spicy_1
            "tags": "lẩu thái cay sa tế hải sản",
            "diemTrungBinh": 8.8,
            "diemChatLuong": 8.8,
            "reviewsCount": 0,
            "price": 180000,
            "lat": 10.7769,
            "lon": 106.7009,
            "address": "123 Lê Lợi, Quận 1",
            "district": "Quận 1",
        },
        # --- Vegetarian (Chay) ---
        {
            "id": "r_veg_1",
            "name": "Cơm Chay Thanh Lương",
            "tags": "cơm chay vegan vegetarian thanh đạm rau củ nấm đậu hũ",
            "diemTrungBinh": 4.8,
            "reviewsCount": 31,
            "price": 45000,
            "lat": 10.7775,
            "lon": 106.7012,
            "address": "22 Nguyễn Huệ, Quận 1",
            "district": "Quận 1",
        },
        {
            "id": "r_veg_2",
            "name": "Lẩu Nấm Chay An Nhiên",
            "tags": "lẩu chay nấm rau củ vegetarian nóng thanh đạm",
            "diemTrungBinh": 9.2,
            "diemChatLuong": 9.3,
            "reviewsCount": 0,
            "price": 120000,
            "lat": 10.7790,
            "lon": 106.6990,
            "address": "10 Lý Tự Trọng, Quận 1",
            "district": "Quận 1",
        },
        {
            "id": "r_veg_3",
            "name": "Bún Chay Sen Vàng",
            "tags": "bún chay vegan thanh mát rau củ",
            "diemTrungBinh": 4.2,
            "reviewsCount": 12,
            "price": 35000,
            "lat": 10.7740,
            "lon": 106.6980,
            "address": "77 Hàm Nghi, Quận 1",
            "district": "Quận 1",
        },
        # --- Non-vegetarian trap with mushroom/veggies ---
        {
            "id": "r_meat_mushroom",
            "name": "Lẩu Gà Nấm Phú Yên",
            "tags": "lẩu gà nấm rau củ thịt gà nước dùng nóng",
            "diemTrungBinh": 9.4,
            "diemChatLuong": 9.4,
            "reviewsCount": 0,
            "price": 195000,
            "lat": 10.7765,
            "lon": 106.7005,
            "address": "19 Đồng Khởi, Quận 1",
            "district": "Quận 1",
        },
        # --- Traditional Phở / Bún / Cơm (Umami / Salty / Budget) ---
        {
            "id": "r_pho_1",
            "name": "Phở Bò Gia Truyền",
            "tags": "phở bò nước dùng bắp bò hầm nóng truyền thống",
            "diemTrungBinh": 4.7,
            "reviewsCount": 42,
            "price": 60000,
            "lat": 10.7768,
            "lon": 106.7011,
            "address": "15 Hai Bà Trưng, Quận 1",
            "district": "Quận 1",
        },
        {
            "id": "r_pho_2_dup",
            "name": "Phở Bò Gia Truyền",  # Duplicate of r_pho_1
            "tags": "phở bò nước dùng",
            "diemTrungBinh": 4.5,
            "reviewsCount": 10,
            "price": 60000,
            "lat": 10.7768,
            "lon": 106.7011,
            "address": "15 Hai Bà Trưng, Quận 1",
            "district": "Quận 1",
        },
        {
            "id": "r_com_1",
            "name": "Cơm Tấm Ba Ghiền",
            "tags": "cơm tấm sườn nướng thịt kho nước mắm mặn đậm đà",
            "diemTrungBinh": 4.5,
            "reviewsCount": 55,
            "price": 55000,
            "lat": 10.7932,
            "lon": 106.6780,
            "address": "84 Đặng Văn Ngữ, Phú Nhuận",
            "district": "Phú Nhuận",
        },
        {
            "id": "r_com_budget",
            "name": "Cơm Bình Dân Cô Ba",
            "tags": "cơm thịt kho cá kho canh chua giá rẻ bình dân",
            "diemTrungBinh": 4.1,
            "reviewsCount": 18,
            "price": 30000,
            "lat": 10.7755,
            "lon": 106.7002,
            "address": "5 Tôn Đức Thắng, Quận 1",
            "district": "Quận 1",
        },
        {
            "id": "r_bun_thit_nuong",
            "name": "Bún Thịt Nướng Kiều Bảo",
            "tags": "bún thịt nướng nước mắm chua ngọt nem nướng",
            "diemTrungBinh": 8.4,
            "diemChatLuong": 8.5,
            "reviewsCount": 0,
            "price": 45000,
            "lat": 10.7720,
            "lon": 106.6950,
            "address": "112 Đề Thám, Quận 1",
            "district": "Quận 1",
        },
        # --- Sweet / Dessert / Cafe ---
        {
            "id": "r_sweet_1",
            "name": "Chè Khúc Bạch Thanh",
            "tags": "chè ngọt thanh mát giải nhiệt kem sữa đường",
            "diemTrungBinh": 4.6,
            "reviewsCount": 29,
            "price": 35000,
            "lat": 10.7770,
            "lon": 106.7018,
            "address": "33 Mạc Thị Bưởi, Quận 1",
            "district": "Quận 1",
        },
        {
            "id": "r_sweet_2",
            "name": "Trà Sữa Phúc Long",
            "tags": "trà sữa ngọt bánh kem giải nhiệt đường sữa",
            "diemTrungBinh": 8.6,
            "diemChatLuong": 8.7,
            "reviewsCount": 0,
            "price": 55000,
            "lat": 10.7760,
            "lon": 106.7022,
            "address": "63 Ngô Đức Kế, Quận 1",
            "district": "Quận 1",
        },
        {
            "id": "r_cafe_bitter",
            "name": "Cà Phê Vợt Chú Ba",
            "tags": "cà phê đắng truyền thống trà đen",
            "diemTrungBinh": 4.4,
            "reviewsCount": 14,
            "price": 25000,
            "lat": 10.7785,
            "lon": 106.6995,
            "address": "9 Phan Kế Bính, Quận 1",
            "district": "Quận 1",
        },
        # --- Sour / Sweet-Sour ---
        {
            "id": "r_sour_1",
            "name": "Canh Chua Cá Lóc Miền Tây",
            "tags": "canh chua me chanh cá kho mặn thịt kho",
            "diemTrungBinh": 8.2,
            "diemChatLuong": 8.0,
            "reviewsCount": 0,
            "price": 75000,
            "lat": 10.7745,
            "lon": 106.7030,
            "address": "41 Hồ Tùng Mậu, Quận 1",
            "district": "Quận 1",
        },
        {
            "id": "r_sour_2",
            "name": "Ốc Đào Nguyễn Trãi",
            "tags": "ốc hải sản tôm cua sốt me chua cay nướng muối ớt",
            "diemTrungBinh": 4.7,
            "reviewsCount": 63,
            "price": 150000,
            "lat": 10.7680,
            "lon": 106.6920,
            "address": "212B Nguyễn Trãi, Quận 1",
            "district": "Quận 1",
        },
        # --- Halal ---
        {
            "id": "r_halal_1",
            "name": "Halal Amin Sài Gòn",
            "tags": "halal muslim cơm bò nướng nước dùng",
            "diemTrungBinh": 4.6,
            "reviewsCount": 19,
            "price": 110000,
            "lat": 10.7750,
            "lon": 106.7010,
            "address": "31 Đông Du, Quận 1",
            "district": "Quận 1",
        },
        # --- Far GPS / High Price ---
        {
            "id": "r_far_thuduc",
            "name": "Bún Bò Huế Thủ Đức",
            "tags": "bún bò nước dùng cay nóng thịt bò",
            "diemTrungBinh": 8.0,
            "diemChatLuong": 8.0,
            "reviewsCount": 0,
            "price": 50000,
            "lat": 10.8505,
            "lon": 106.7719,  # ~11.2 km from Q1
            "address": "15 Võ Văn Ngân, Thủ Đức",
            "district": "Thủ Đức",
        },
        {
            "id": "r_upscale_1",
            "name": "Nhà Hàng Hải Sản Bến Thành",
            "tags": "hải sản tôm cua nướng lẩu tiếp khách sang trọng",
            "diemTrungBinh": 9.4,
            "diemChatLuong": 9.5,
            "reviewsCount": 0,
            "price": 450000,
            "lat": 10.7730,
            "lon": 106.6980,
            "address": "2 Lê Lai, Quận 1",
            "district": "Quận 1",
        },
        # --- Poor Foody restaurant with <= 5.0 raw score ---
        {
            "id": "r_poor_foody_pho",
            "name": "Phở Đêm Vỉa Hè",
            "tags": "phở bò nước dùng nóng",
            "diemTrungBinh": 4.0,  # 4.0/10 Foody -> 2.0/5
            "diemChatLuong": 3.8,
            "reviewsCount": 0,
            "price": 45000,
            "lat": 10.7765,
            "lon": 106.7010,
            "address": "99 Calmette, Quận 1",
            "district": "Quận 1",
        },
    ]


def build_normalized_catalog_df() -> pd.DataFrame:
    """Build normalized catalog DataFrame exactly as mongo.py does."""
    raw_docs = get_raw_synthetic_restaurants()
    rows = []
    for doc in raw_docs:
        scale, raw_val = detect_restaurant_rating_scale(doc)
        norm_val = normalize_rating(raw_val, scale=scale)
        row = dict(doc)
        row["raw_rating"] = raw_val
        row["raw_rating_scale"] = scale.value
        row["rating"] = norm_val
        row["_rating_normalized"] = True
        rows.append(row)
    return pd.DataFrame(rows)


def build_baseline_naive_catalog_df() -> pd.DataFrame:
    """Build catalog DataFrame using the pre-M7.1 naive >5.0 rating normalization."""
    raw_docs = get_raw_synthetic_restaurants()
    rows = []
    for doc in raw_docs:
        raw_val = float(doc.get("diemTrungBinh", 3.5))
        naive_norm = round(raw_val / 2.0, 1) if raw_val > 5.0 else round(raw_val, 1)
        row = dict(doc)
        row["rating"] = naive_norm
        rows.append(row)
    return pd.DataFrame(rows)


def get_synthetic_cf_interactions() -> List[Dict[str, Any]]:
    """
    Synthetic interaction records for CollaborativeFilteringEngine:
    - u_warm_spicy: 4 interactions (sufficient CF history >= 2)
    - u_warm_sweet: 3 interactions (sufficient CF history >= 2)
    - u_low_hist: 1 interaction (< 2 -> treated as cold-start)
    - u_cold_zero: 0 interactions (cold-start)
    """
    return [
        {"userId": "u_warm_spicy", "targetId": "r_spicy_1", "eventType": "REVIEW", "rating": 9.2},
        {"userId": "u_warm_spicy", "targetId": "r_spicy_2", "eventType": "FAVORITE"},
        {"userId": "u_warm_spicy", "targetId": "r_sour_2", "eventType": "SAVE"},
        {"userId": "u_warm_spicy", "targetId": "r_meat_mushroom", "eventType": "VIEW"},
        {"userId": "u_warm_sweet", "targetId": "r_sweet_1", "eventType": "REVIEW", "rating": 4.8},
        {"userId": "u_warm_sweet", "targetId": "r_sweet_2", "eventType": "FAVORITE"},
        {"userId": "u_warm_sweet", "targetId": "r_bun_thit_nuong", "eventType": "CLICK"},
        {"userId": "u_low_hist", "targetId": "r_pho_1", "eventType": "VIEW"},
        # Extra users so TruncatedSVD has >= 2 factors
        {"userId": "u_aux_1", "targetId": "r_pho_1", "eventType": "REVIEW", "rating": 4.9},
        {"userId": "u_aux_1", "targetId": "r_com_1", "eventType": "SAVE"},
        {"userId": "u_aux_2", "targetId": "r_veg_1", "eventType": "REVIEW", "rating": 4.8},
        {"userId": "u_aux_2", "targetId": "r_veg_2", "eventType": "FAVORITE"},
    ]


def get_synthetic_user_profiles() -> List[Dict[str, Any]]:
    """
    10 diverse synthetic user profiles with graded relevance ground truth:
    Grades: 3 = highly relevant, 2 = relevant, 1 = marginally relevant, 0 = irrelevant.
    """
    return [
        {
            "user_id": "u_warm_spicy",
            "label": "Spicy Food Lover (Warm CF)",
            "taste_vector": [0.95, 0.1, 0.3, 0.3, 0.6, 0.1],
            "dietary_exclusions": [],
            "max_price": None,
            "user_gps": [10.7769, 106.7009],
            "weather_type": "rainy",
            "temperature": 23.0,
            "relevance_grades": {
                "r_spicy_1": 3,
                "r_spicy_2": 3,
                "r_sour_2": 2,
                "r_far_thuduc": 1,
                # r_spicy_3_poor_foody is 3.8/10 -> poor quality, grade 0
            },
        },
        {
            "user_id": "u_veg_strict",
            "label": "Strict Vegetarian User",
            "taste_vector": [0.1, 0.2, 0.2, 0.3, 0.4, 0.1],
            "dietary_exclusions": ["chay"],
            "max_price": 150000,
            "user_gps": [10.7769, 106.7009],
            "weather_type": "cool",
            "temperature": 26.0,
            "relevance_grades": {
                "r_veg_1": 3,
                "r_veg_2": 3,
                "r_veg_3": 2,
            },
        },
        {
            "user_id": "u_budget_tight",
            "label": "Budget-Sensitive Student (<= 50k VND)",
            "taste_vector": [0.2, 0.3, 0.2, 0.5, 0.5, 0.1],
            "dietary_exclusions": [],
            "max_price": 50000,
            "user_gps": [10.7769, 106.7009],
            "weather_type": "neutral",
            "temperature": 28.0,
            "relevance_grades": {
                "r_com_budget": 3,
                "r_bun_thit_nuong": 3,
                "r_veg_1": 2,
                "r_sweet_1": 2,
                "r_veg_3": 2,
                "r_cafe_bitter": 1,
            },
        },
        {
            "user_id": "u_gps_nearby",
            "label": "Nearby Q1 Traditional Noodle Lover",
            "taste_vector": [0.2, 0.1, 0.1, 0.4, 0.9, 0.1],
            "dietary_exclusions": [],
            "max_price": 100000,
            "user_gps": [10.7768, 106.7010],
            "weather_type": "rainy",
            "temperature": 24.0,
            "relevance_grades": {
                "r_pho_1": 3,
                "r_spicy_2": 2,
                "r_com_budget": 2,
                "r_bun_thit_nuong": 2,
            },
        },
        {
            "user_id": "u_multi_taste",
            "label": "Sweet & Sour Multi-Taste Explorer",
            "taste_vector": [0.2, 0.85, 0.85, 0.2, 0.3, 0.1],
            "dietary_exclusions": [],
            "max_price": 160000,
            "user_gps": [10.7769, 106.7009],
            "weather_type": "hot",
            "temperature": 33.0,
            "relevance_grades": {
                "r_sweet_1": 3,
                "r_sweet_2": 3,
                "r_sour_1": 2,
                "r_sour_2": 2,
                "r_bun_thit_nuong": 2,
            },
        },
        {
            "user_id": "u_cold_zero",
            "label": "Cold-Start User (0 interactions, Umami)",
            "taste_vector": [0.2, 0.1, 0.1, 0.5, 0.9, 0.1],
            "dietary_exclusions": [],
            "max_price": 200000,
            "user_gps": [10.7769, 106.7009],
            "weather_type": "neutral",
            "temperature": 28.0,
            "relevance_grades": {
                "r_pho_1": 3,
                "r_meat_mushroom": 2,
                "r_com_1": 2,
                "r_com_budget": 2,
                "r_halal_1": 1,
            },
        },
        {
            "user_id": "u_low_hist",
            "label": "Low-History User (1 interaction < 2, Cold-Start)",
            "taste_vector": [0.1, 0.2, 0.2, 0.4, 0.85, 0.1],
            "dietary_exclusions": [],
            "max_price": 120000,
            "user_gps": [10.7769, 106.7009],
            "weather_type": "rainy",
            "temperature": 24.0,
            "relevance_grades": {
                "r_pho_1": 3,
                "r_com_1": 2,
                "r_com_budget": 2,
                "r_halal_1": 1,
            },
        },
        {
            "user_id": "u_warm_sweet",
            "label": "Dessert & Refreshing Food Lover (Warm CF)",
            "taste_vector": [0.1, 0.95, 0.3, 0.1, 0.2, 0.1],
            "dietary_exclusions": [],
            "max_price": 100000,
            "user_gps": [10.7769, 106.7009],
            "weather_type": "hot",
            "temperature": 34.0,
            "relevance_grades": {
                "r_sweet_1": 3,
                "r_sweet_2": 3,
                "r_bun_thit_nuong": 1,
            },
        },
        {
            "user_id": "u_non_spicy",
            "label": "Non-Spicy Preference User",
            "taste_vector": [0.0, 0.3, 0.2, 0.5, 0.8, 0.1],
            "dietary_exclusions": ["không cay"],
            "max_price": 120000,
            "user_gps": [10.7769, 106.7009],
            "weather_type": "neutral",
            "temperature": 27.0,
            "relevance_grades": {
                "r_pho_1": 3,
                "r_com_budget": 2,
                "r_bun_thit_nuong": 2,
                "r_com_1": 2,
                "r_veg_1": 1,
            },
        },
        {
            "user_id": "u_halal_user",
            "label": "Halal Dietary Restriction User",
            "taste_vector": [0.3, 0.2, 0.2, 0.4, 0.8, 0.1],
            "dietary_exclusions": ["halal"],
            "max_price": 200000,
            "user_gps": [10.7769, 106.7009],
            "weather_type": "neutral",
            "temperature": 28.0,
            "relevance_grades": {
                "r_halal_1": 3,
            },
        },
    ]
