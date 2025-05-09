from fastapi import APIRouter
import logging

router = APIRouter(prefix="/api/health", tags=["System"])

logger = logging.getLogger(__name__)

@router.get("/")
async def health_check():
    logger.info("Health check request received")
    return {"status": "ok3"}