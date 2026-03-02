from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["health"])

@router.get("/health", summary="Service health check")
async def health():
    return {"status": "ok", "service": "chama-api", "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()}
