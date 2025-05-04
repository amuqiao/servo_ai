from fastapi import APIRouter

router = APIRouter(prefix="/api/health", tags=["System"])

@router.get("/")
async def health_check():
    return {"status": "ok2"}