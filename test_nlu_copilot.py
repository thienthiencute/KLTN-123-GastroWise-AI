"""
Unit Test cho TASK-P5-01: Multi-Intent NLU & Dialogue Orchestrator (AI Food Copilot)
"""
from app.core.nlu_service import classify_intent, process_copilot_dialogue

def test_intent_classification():
    # Test 1: Nutrition Query
    intent, entities = classify_intent("Cho mình hỏi một tô phở bò bao nhiêu calo vậy?")
    assert intent == "ask_nutrition", f"Expected ask_nutrition, got {intent}"
    assert entities.get("dish_name") in ["phở bò", "phở", "pho bo"]

    # Test 2: Journey Planning
    intent2, entities2 = classify_intent("Lên lịch trình ăn vặt chiều nay tại Quận 1 ngân sách 200k")
    assert intent2 == "plan_journey", f"Expected plan_journey, got {intent2}"
    assert entities2.get("district") == "Quận 1"
    assert entities2.get("budget") == 200000

    # Test 3: Find Nearby
    intent3, entities3 = classify_intent("Có quán nào ngon quanh đây không bạn?")
    assert intent3 == "find_nearby", f"Expected find_nearby, got {intent3}"

    # Test 4: General Greeting
    intent4, _ = classify_intent("Xin chào bạn")
    assert intent4 == "general_greeting", f"Expected general_greeting, got {intent4}"

    # Test 5: Search Food
    intent5, entities5 = classify_intent("Tìm quán lẩu nướng ở Bình Thạnh")
    assert intent5 == "search_food", f"Expected search_food, got {intent5}"
    assert entities5.get("district") == "Bình Thạnh"

    print("-> Tất cả 5 intent test cases PASS xuất sắc!")

def test_dialogue_orchestrator():
    # Dialogue 1: Nutrition Action Card
    res1 = process_copilot_dialogue("bánh mì có bao nhiêu calo?")
    assert res1['intent'] == 'ask_nutrition'
    assert res1['action_card'] is not None
    assert res1['action_card']['type'] == 'nutrition_card'
    assert res1['action_card']['calories'] == 385

    # Dialogue 2: Planner Action Card
    res2 = process_copilot_dialogue("lập food tour ở Quận 3 khoảng 300k")
    assert res2['intent'] == 'plan_journey'
    assert res2['action_card'] is not None
    assert res2['action_card']['type'] == 'planner_action'
    assert res2['action_card']['district'] == 'Quận 3'
    assert res2['action_card']['budget'] == 300000

    # Dialogue 3: Greeting
    res3 = process_copilot_dialogue("xin chào")
    assert res3['intent'] == 'general_greeting'
    assert res3['action_card']['type'] == 'quick_prompts'

    print("-> Dialogue Orchestrator Action Cards PASS 100%!")

if __name__ == "__main__":
    test_intent_classification()
    test_dialogue_orchestrator()

