from fastapi import APIRouter

from app.api.v1.media.router import router as media_router

router = APIRouter()

router.include_router(media_router)
