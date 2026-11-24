import os
import secrets
from fastapi import Request, HTTPException, status

async def verify_internal_ai_key(request: Request):
    """
    Verifies mutual authentication header X-Internal-AI-Key.
    Uses timing-safe comparison (secrets.compare_digest).
    Enforces fail-closed: If INTERNAL_AI_KEY is not set in environment,
    it raises a 500 error to prevent unauthenticated traffic.
    """
    expected_key = os.getenv("INTERNAL_AI_KEY")
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal configuration error: INTERNAL_AI_KEY is not configured",
        )

    provided_key = request.headers.get("X-Internal-AI-Key")
    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Internal-AI-Key header",
        )

    if not secrets.compare_digest(provided_key.encode("utf-8"), expected_key.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal AI service key",
        )
    return True
