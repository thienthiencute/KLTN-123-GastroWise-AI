from fastapi import APIRouter
from app.schemas.copilot import CopilotChatRequest, CopilotChatResponse
from app.core.nlu_service import process_copilot_dialogue

router = APIRouter(tags=["Copilot"])

@router.post("/message", response_model=CopilotChatResponse)
async def handle_copilot_message(request_data: CopilotChatRequest):
    """
    [TASK-P5-01] AI Natural Language Food Copilot Message Handler:
    Phân tích ý định người dùng (search_food, plan_journey, ask_nutrition, find_nearby),
    trích xuất slots và trả về câu trả lời kèm Action Card tương tác cho Mobile.
    """
    res = process_copilot_dialogue(
        message=request_data.message,
        user_gps=request_data.user_gps,
        taste_vector=request_data.taste_vector
    )
    return CopilotChatResponse(
        reply=res['reply'],
        intent=res['intent'],
        entities=res['entities'],
        action_card=res.get('action_card'),
        results=res.get('results', [])
    )

