from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.agents import router as agents_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.evaluations import router as evaluations_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.reports import router as reports_router
from app.api.v1.health import router as health_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(agents_router)
api_router.include_router(datasets_router)
api_router.include_router(evaluations_router)
api_router.include_router(analytics_router)
api_router.include_router(reports_router)
api_router.include_router(health_router)
