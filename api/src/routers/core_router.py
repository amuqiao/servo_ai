from fastapi import APIRouter
from .user_router import router as user_router

core_router = APIRouter()

core_router.include_router(user_router)