from fastapi import FastAPI
from app.config import settings
from app.api.v1 import calendar, sessions

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    description="Calendar Sessions Management API - supports one-time and recurring sessions",
)


@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {"message": "Calendar Sessions API", "version": settings.APP_VERSION, "status": "ok", "docs": "/docs"}


@app.get("/health", tags=["health"])
async def health_check():
    """Health check for monitoring"""
    return {"status": "healthy"}


# Include routers
app.include_router(calendar.router, prefix=settings.API_V1_PREFIX, tags=["calendar"])
app.include_router(sessions.router, prefix=settings.API_V1_PREFIX, tags=["sessions"])
