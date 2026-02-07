from fastapi import APIRouter

from app.api.v1.endpoints import auth, calendar, dashboard, email_credentials, email_scanner, finance, news, packages, servers, weather

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(servers.router)
api_router.include_router(packages.router)
api_router.include_router(finance.router)
api_router.include_router(weather.router)
api_router.include_router(news.router)
api_router.include_router(calendar.router)
api_router.include_router(email_scanner.router)
api_router.include_router(email_credentials.router)


@api_router.get("/")
def root():
    return {"message": "Personal Dash API v1"}
