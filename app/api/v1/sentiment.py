from fastapi import APIRouter
from app.schemas.sentiment import SentimentRequest, SentimentResponse, AdvancedSentimentResponse
from app.core.sentiment_service import analyze_sentiment_visobert, analyze_sentiment_rule_based

router = APIRouter(tags=["Sentiment Analysis"])

@router.post("/sentiment", response_model=SentimentResponse)
async def handle_sentiment(request_data: SentimentRequest):
    return analyze_sentiment_visobert(request_data)

@router.post("/analyze-sentiment", response_model=AdvancedSentimentResponse)
async def handle_analyze_sentiment(request_data: SentimentRequest):
    return analyze_sentiment_rule_based(request_data)
