from fastapi import APIRouter

router = APIRouter()

# ─── Add v1 endpoint modules here as the API grows ───────────────────────────
# from app.api.v1.endpoints import users, items
# router.include_router(users.router, prefix="/users", tags=["users"])
# router.include_router(items.router, prefix="/items", tags=["items"])
