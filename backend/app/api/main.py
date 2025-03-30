from fastapi import APIRouter

from app.api.routes import  login, private, products, users, utils, gamification, interaction
from app.core.postgres.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(gamification.router)
api_router.include_router(interaction.router)
api_router.include_router(products.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
