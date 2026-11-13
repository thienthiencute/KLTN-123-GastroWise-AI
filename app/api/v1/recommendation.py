from fastapi import APIRouter
from app.schemas.recommendation import (
    RecommendRequest, RecommendResponse, 
    ChatRequest, ChatResponse,
    HybridRecommendRequest, HybridRecommendResponse,
    TrainCFRequest, TrainCFResponse
)
from app.core.recommender import recommend_restaurants, recommend_hybrid
from app.core.collaborative_filter import cf_engine

router = APIRouter(tags=["Recommendation"])

@router.post("/recommend", response_model=RecommendResponse)
async def handle_recommendation(request_data: RecommendRequest):
    return recommend_restaurants(request_data)

@router.post("/recommend/hybrid", response_model=HybridRecommendResponse)
async def handle_hybrid_recommendation(request_data: HybridRecommendRequest):
    """
    [TASK-P2-01 & TASK-P2-02] 4-Stage Industrial Hybrid AI Recommendation:
    - Stage 1: Candidate Generation & Hard Constraints (Geo, Price, Dietary)
    - Stage 2: Content-Based Taste DNA 6-D Vector Cosine Similarity
    - Stage 3: SVD Collaborative Filtering
    - Stage 4: Contextual Weather Boost & Distance Decay Ranking with Explainability Pills
    """
    return recommend_hybrid(request_data)

@router.post("/cf/train", response_model=TrainCFResponse)
async def handle_train_cf(request_data: TrainCFRequest):
    """
    [TASK-P2-02] Huấn luyện / cập nhật lại mô hình TruncatedSVD Collaborative Filtering
    từ ma trận tương tác người dùng - nhà hàng.
    """
    success = cf_engine.train_from_interactions(request_data.interactions)
    u_count = len(cf_engine.user_to_idx)
    i_count = len(cf_engine.item_to_idx)
    return TrainCFResponse(
        success=success,
        message="Huấn luyện mô hình Collaborative Filtering thành công" if success else "Chưa đủ dữ liệu để huấn luyện SVD",
        user_count=u_count,
        item_count=i_count
    )

@router.post("/chat", response_model=ChatResponse)
async def handle_chat(request_data: ChatRequest):
    rec_req = RecommendRequest(
        query=request_data.message, 
        user_gps=request_data.user_gps,
        taste_vector=request_data.taste_vector
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
