"""路由聚合。"""
from fastapi import APIRouter

from app.api import admin_models, auth, previz, projects, reference_shots, reviews

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(previz.router)
api_router.include_router(reference_shots.router)
api_router.include_router(reviews.router)
api_router.include_router(reviews.public_router)
api_router.include_router(admin_models.router)
