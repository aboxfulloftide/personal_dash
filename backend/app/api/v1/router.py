from fastapi import APIRouter

from app.api.v1.endpoints import auth, dashboard

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(dashboard.router)


@api_router.get("/")
def root():
    return {"message": "Personal Dash API v1"}
