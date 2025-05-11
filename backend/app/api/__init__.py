from fastapi import APIRouter

from app.api.users import router as users_router
from app.api.models import router as models_router
from app.api.predictions import router as predictions_router

api_router = APIRouter()

api_router.include_router(users_router, tags=["users"])
api_router.include_router(models_router, tags=["models"])
api_router.include_router(predictions_router, tags=["predictions"])
