from transformers import pipeline
from app.schemas.sentiment import SentimentRequest, SentimentResponse, AdvancedSentimentResponse

# Lazy pipeline singleton
_sentiment_pipeline = None

def get_sentiment_pipeline():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        try:
            print("-> Loading Vietnamese Sentiment ViSoBERT Pipeline...")
            _sentiment_pipeline = pipeline("sentiment-analysis", model="5CD-AI/Vietnamese-Sentiment-visobert")
        except Exception as e:
            print(f"!!! Không thể load ViSoBERT model: {e}")
            _sentiment_pipeline = False
    return _sentiment_pipeline if _sentiment_pipeline is not False else None

def analyze_sentiment_visobert(request_data: SentimentRequest) -> SentimentResponse:
    pipe = get_sentiment_pipeline()
    if not pipe:
        return SentimentResponse(label="neutral", score=0.5)
    try:
        res = pipe(request_data.review)[0]
        return SentimentResponse(label=res['label'], score=float(res['score']))
    except Exception:
        return SentimentResponse(label="neutral", score=0.5)

def analyze_sentiment_rule_based(req: SentimentRequest) -> AdvancedSentimentResponse:
    content = req.review or ""
    lower = content.lower()
    
    pos_words = ["ngon", "tuyệt", "sạch", "thích", "chu đáo", "nhiệt tình", "rẻ", "hợp lý", "chất lượng", "5 sao", "5*", "quay lại", "đậm vị", "hài lòng"]
    neg_words = ["dở", "tệ", "mặn", "nhạt", "bẩn", "tệ hại", "đắt", "chậm", "thái độ", "không bao giờ", "thất vọng", "1 sao", "1*"]
    
    pos_count = sum(1 for w in pos_words if w in lower)
    neg_count = sum(1 for w in neg_words if w in lower)
    
    if pos_count > neg_count:
        label = "POSITIVE"
        score = min(0.99, 0.7 + pos_count * 0.1)
    elif neg_count > pos_count:
        label = "NEGATIVE"
        score = max(0.1, 0.4 - neg_count * 0.1)
    else:
        label = "NEUTRAL"
        score = 0.5
        
    hashtags = []
    if "ngon" in lower: hashtags.append("#monngon")
    if "sạch" in lower: hashtags.append("#sachse")
    if "nhiệt tình" in lower or "chu đáo" in lower: hashtags.append("#phucvutot")
    if "rẻ" in lower or "hợp lý" in lower: hashtags.append("#giacahoply")
    if "đẹp" in lower or "thoáng" in lower: hashtags.append("#khonggian_dep")
    
    return AdvancedSentimentResponse(
        label=label,
        score=round(score, 2),
        hashtags=hashtags[:3]
    )
