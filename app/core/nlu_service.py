import re
from typing import Dict, Any, List, Optional, Tuple
from app.core.nutrition_data import VIETNAMESE_FOOD_NUTRITION
from app.core.recommender import recommend_restaurants, recommend_hybrid
from app.schemas.recommendation import HybridRecommendRequest, RecommendRequest

# Danh sách quận/huyện TP.HCM phục vụ slot filling
DISTRICT_PATTERNS = {
    'Quận 1': ['quận 1', 'q1', 'q 1', 'quan 1'],
    'Quận 3': ['quận 3', 'q3', 'q 3', 'quan 3'],
    'Quận 4': ['quận 4', 'q4', 'q 4', 'quan 4'],
    'Quận 5': ['quận 5', 'q5', 'q 5', 'quan 5'],
    'Quận 7': ['quận 7', 'q7', 'q 7', 'quan 7'],
    'Quận 10': ['quận 10', 'q10', 'q 10', 'quan 10'],
    'Bình Thạnh': ['bình thạnh', 'binh thanh', 'bthanh'],
    'Gò Vấp': ['gò vấp', 'go vap', 'gv'],
    'Thủ Đức': ['thủ đức', 'thu duc'],
    'Tân Bình': ['tân bình', 'tan binh'],
    'Phú Nhuận': ['phú nhuận', 'phu nhuan'],
}

def extract_budget_slot(text: str) -> Optional[int]:
    """Trích xuất ngân sách (ví dụ: 'dưới 200k', '300.000', '150k')"""
    text_lower = text.lower()
    # [Fix budget regex] 'k' không được nối liền với chữ cái tiếng Việt (tránh nhầm 'quận 3 khoảng' thành 3k)
    match = re.search(r'(\d+)\s*(k(?![a-zA-Z\u00C0-\u024F\u1EA0-\u1EF9])|nghìn|ngàn|tram|trăm)', text_lower)
    if match:
        val = int(match.group(1))
        unit = match.group(2)
        if unit.startswith('k') or unit in ['nghìn', 'ngàn']:
            return val * 1000
        if unit in ['tram', 'trăm']:
            return val * 100000

    match_exact = re.search(r'(\d{2,3})[.,](\d{3})', text_lower)
    if match_exact:
        return int(match_exact.group(1) + match_exact.group(2))

    return None

def extract_district_slot(text: str) -> Optional[str]:
    """Trích xuất khu vực / quận huyện"""
    text_lower = text.lower()
    for district, patterns in DISTRICT_PATTERNS.items():
        if any(p in text_lower for p in patterns):
            return district
    return None

def extract_dish_for_nutrition(text: str) -> Optional[str]:
    """Tìm món ăn có trong bảng dinh dưỡng từ câu hỏi người dùng"""
    text_lower = text.lower()
    # Sắp xếp theo độ dài giảm dần để ưu tiên cụm từ dài (vd 'bún bò huế' trước 'bún')
    sorted_dishes = sorted(VIETNAMESE_FOOD_NUTRITION.keys(), key=len, reverse=True)
    for dish in sorted_dishes:
        if dish in text_lower:
            return dish
    return None

def classify_intent(query: str) -> Tuple[str, Dict[str, Any]]:
    """
    [TASK-P5-01] Phân loại ý định người dùng (Intent Classification) & Trích xuất thực thể (Slot Filling)
    """
    q_lower = query.lower().strip()
    entities: Dict[str, Any] = {}

    # Extract slots
    district = extract_district_slot(q_lower)
    if district:
        entities['district'] = district

    budget = extract_budget_slot(q_lower)
    if budget:
        entities['budget'] = budget

    # 1. INTENT: ASK_NUTRITION (Hỏi calo, dinh dưỡng, béo)
    nutrition_keywords = ['calo', 'calories', 'dinh dưỡng', 'chất đạm', 'protein', 'béo', 'bao nhiêu calo', 'ăn có mập']
    if any(kw in q_lower for kw in nutrition_keywords):
        dish = extract_dish_for_nutrition(q_lower)
        if dish:
            entities['dish_name'] = dish
            return 'ask_nutrition', entities

    # 2. INTENT: PLAN_JOURNEY (Lên lịch trình, tour ẩm thực, lộ trình)
    journey_keywords = ['lịch trình', 'lộ trình', 'tour', 'lên tour', 'kế hoạch ăn', 'ăn cả ngày', 'food tour', 'đi ăn']
    if any(kw in q_lower for kw in journey_keywords):
        return 'plan_journey', entities

    # 3. INTENT: FIND_NEARBY (Tìm quanh đây, gần đây, gần vị trí)
    nearby_keywords = ['gần đây', 'gần tôi', 'quanh đây', 'gần nhất', 'xung quanh']
    if any(kw in q_lower for kw in nearby_keywords):
        return 'find_nearby', entities

    # 4. INTENT: GREETING / FAQ
    greeting_keywords = ['xin chào', 'hello', 'hi', 'bạn là ai', 'có thể làm gì', 'giúp gì', 'hướng dẫn']
    if any(q_lower == kw or q_lower.startswith(kw) for kw in greeting_keywords) and len(q_lower.split()) <= 4:
        return 'general_greeting', entities

    # 5. INTENT: SEARCH_FOOD (Mặc định tìm món ăn / nhà hàng)
    return 'search_food', entities

def process_copilot_dialogue(
    message: str,
    user_gps: Optional[List[float]] = None,
    taste_vector: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Điều phối hội thoại AI Food Copilot (Dialogue Orchestrator):
    Xác định ý định, tìm kiếm dữ liệu phù hợp, và trả về Action Card tương tác cho Mobile UI.
    """
    intent, entities = classify_intent(message)

    # -------------------------------------------------------------------------
    # CASE 1: ASK_NUTRITION
    # -------------------------------------------------------------------------
    if intent == 'ask_nutrition':
        dish_name = entities.get('dish_name')
        nutri_info = VIETNAMESE_FOOD_NUTRITION.get(dish_name, None) if dish_name else None

        if nutri_info:
            reply_text = (
                f"Thông tin dinh dưỡng cho món {dish_name.title()}:\n"
                f"• Khẩu phần: {nutri_info.get('serving_desc', '1 phần chuẩn')}\n"
                f"• Năng lượng: {nutri_info['calories']} kcal\n"
                f"• Đạm (Protein): {nutri_info['protein_g']}g\n"
                f"• Tinh bột (Carbs): {nutri_info['carbs_g']}g\n"
                f"• Chất béo (Fat): {nutri_info['fat_g']}g\n\n"
                f"Bạn có muốn mình tìm các quán bán {dish_name.title()} ngon gần bạn không?"
            )
            action_card = {
                'type': 'nutrition_card',
                'title': f'Dinh Dưỡng: {dish_name.title()}',
                'calories': nutri_info['calories'],
                'protein_g': nutri_info['protein_g'],
                'carbs_g': nutri_info['carbs_g'],
                'fat_g': nutri_info['fat_g'],
                'serving': nutri_info.get('serving_desc', ''),
                'button_text': f'Tìm quán {dish_name.title()}',
                'action': 'search_dish',
                'query': dish_name
            }
            return {
                'reply': reply_text,
                'intent': intent,
                'entities': entities,
                'action_card': action_card,
                'results': []
            }
        else:
            return {
                'reply': f"GastroWise chưa có bảng calo chính xác cho món bạn hỏi trong ngân hàng 20 món Việt. Bạn có thể chụp ảnh món ăn ở mục 'AI Nutri' để nhận diện tức thì nhé!",
                'intent': intent,
                'entities': entities,
                'action_card': {
                    'type': 'navigate_action',
                    'title': 'AI Camera Nutri',
                    'button_text': 'Mở Camera Quét Món',
                    'action': 'open_ai_nutri'
                },
                'results': []
            }

    # -------------------------------------------------------------------------
    # CASE 2: PLAN_JOURNEY
    # -------------------------------------------------------------------------
    if intent == 'plan_journey':
        district = entities.get('district', 'Quận 1')
        budget = entities.get('budget', 250000)

        reply_text = (
            f"Tuyệt vời! Mình sẵn sàng lên lộ trình Food Tour ẩm thực tại {district} "
            f"với ngân sách khoảng {budget:,.0f}đ cho bạn. "
            f"Thuật toán tối ưu đường đi ngắn nhất (OR-Tools) sẽ sắp xếp các chặng quán hợp lý."
        )
        action_card = {
            'type': 'planner_action',
            'title': f'Lập Lộ Trình Food Tour {district}',
            'district': district,
            'budget': budget,
            'button_text': '🚀 Khởi Tạo Lộ Trình Ngay',
            'action': 'open_planner',
            'params': {
                'district': district,
                'budget': budget
            }
        }
        return {
            'reply': reply_text,
            'intent': intent,
            'entities': entities,
            'action_card': action_card,
            'results': []
        }

    # -------------------------------------------------------------------------
    # CASE 3: FIND_NEARBY
    # -------------------------------------------------------------------------
    if intent == 'find_nearby':
        hybrid_req = HybridRecommendRequest(
            user_gps=user_gps or [10.7769, 106.7009],
            taste_vector=taste_vector,
            limit=4
        )
        rec_res = recommend_hybrid(hybrid_req)
        items = rec_res.items

        reply_text = f"Mình đã quét các quán ăn xuất sắc nhất quanh vị trí của bạn ({len(items)} quán):"
        action_card = {
            'type': 'explore_action',
            'title': 'Khám Phá Nhà Hàng Gần Bạn',
            'button_text': '🗺️ Mở Bản Đồ Quanh Bạn',
            'action': 'open_explore_nearby'
        }
        return {
            'reply': reply_text,
            'intent': intent,
            'entities': entities,
            'action_card': action_card,
            'results': [
                {
                    'id': it.id,
                    'name': it.name,
                    'tags': it.tags,
                    'rating': 4.8,
                    'distance_km': it.distance_km,
                    'price': it.price,
                    'explanation': it.explanation
                } for it in items
            ]
        }

    # -------------------------------------------------------------------------
    # CASE 4: GENERAL_GREETING
    # -------------------------------------------------------------------------
    if intent == 'general_greeting':
        return {
            'reply': (
                "Xin chào! Mình là GastroWise AI Copilot. Mình có thể giúp bạn:\n"
                "1. 🍲 Tìm kiếm món ăn và nhà hàng hợp khẩu vị Taste DNA.\n"
                "2. 🗺️ Lên lịch trình ẩm thực tối ưu đường đi ngắn nhất.\n"
                "3. 🥗 Tra cứu lượng calo & dinh dưỡng món ăn Việt Nam.\n"
                "4. 📍 Gợi ý quán ngon nổi bật quanh vị trí của bạn.\n\n"
                "Hôm nay bạn muốn thưởng thức món gì?"
            ),
            'intent': intent,
            'entities': entities,
            'action_card': {
                'type': 'quick_prompts',
                'title': 'Gợi ý câu hỏi nhanh',
                'prompts': [
                    'Lẩu thái chua cay ở Quận 1',
                    'Lên lịch trình ăn vặt Gò Vấp 200k',
                    'Phở bò bao nhiêu calo?',
                    'Quán ăn ngon gần tôi'
                ]
            },
            'results': []
        }

    # -------------------------------------------------------------------------
    # CASE 5: SEARCH_FOOD (Default)
    # -------------------------------------------------------------------------
    rec_req = RecommendRequest(
        query=message,
        user_gps=user_gps,
        taste_vector=taste_vector,
        city_filter=entities.get('district')
    )
    rec_result = recommend_restaurants(rec_req)
    scores = rec_result.get('scores', [])[:4]

    if scores:
        reply_text = f"Dựa trên yêu cầu '{message}', GastroWise tìm thấy {len(scores)} địa điểm rất phù hợp với bạn:"
    else:
        reply_text = f"Rất tiếc mình chưa tìm thấy quán chính xác cho '{message}'. Bạn thử tìm theo món (lẩu nướng, phở, bún đậu) hoặc khu vực xem nhé!"

    action_card = {
        'type': 'search_results_action',
        'title': f'Kết quả cho: {message}',
        'button_text': 'Xem thêm trên mục Khám phá',
        'action': 'open_explore_search',
        'query': message
    }

    return {
        'reply': reply_text,
        'intent': intent,
        'entities': entities,
        'action_card': action_card,
        'results': [
            {
                'id': it['id'],
                'name': it['name'],
                'tags': it['tags'],
                'rating': 4.8,
                'distance_km': it.get('distance_km', 1.0),
                'price': it['price'],
                'explanation': it.get('explanation', 'Phù hợp yêu cầu tìm kiếm')
            } for it in scores
        ]
    }

