from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class CopilotChatRequest(BaseModel):
    message: str
    user_gps: Optional[List[float]] = None
    taste_vector: Optional[List[float]] = None

class CopilotChatResponse(BaseModel):
    reply: str
    intent: str
    entities: Dict[str, Any]
    action_card: Optional[Dict[str, Any]] = None
    results: List[Dict[str, Any]] = []

