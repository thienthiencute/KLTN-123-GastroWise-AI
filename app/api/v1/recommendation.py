from fastapi import APIRouter
from app.schemas.recommendation import RecommendRequest, RecommendResponse, ChatRequest, ChatResponse
from app.core.recommender import recommend_restaurants

router = APIRouter(tags=["Recommendation"])

@router.post("/recommend", response_model=RecommendResponse)
async def handle_recommendation(request_data: RecommendRequest):
    return recommend_restaurants(request_data)

@router.post("/chat", response_model=ChatResponse)
async def handle_chat(request_data: ChatRequest):
    rec_req = RecommendRequest(
        query=request_data.message, 
        user_gps=request_data.user_gps
    )
    
    rec_result = recommend_restaurants(rec_req)
    scores = rec_result.get('scores', [])
    top_results = scores[:5]
    count = len(top_results)
    
    if count == 0:
        reply = f"Rất tiếc, mình chưa tìm thấy quán nào phù hợp với yêu cầu '{request_data.message}'. Bạn thử đổi từ khóa khác xem sao nhé (ví dụ: 'phở bò', 'cơm tấm')."
    else:
        reply = f"Mình đã tìm được {count} địa điểm phù hợp nhất với yêu cầu '{request_data.message}' của bạn. Mời bạn tham khảo nhé!"

    return ChatResponse(
        reply_text=reply,
        data=top_results
    )
