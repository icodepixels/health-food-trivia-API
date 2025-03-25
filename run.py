from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings, Settings
from app.database import database
from app.routes import questions, quizzes, categories, users
import uvicorn

app = FastAPI(
    title="Quiz API",
    description="A FastAPI-based Quiz application with async database operations",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Include all routers
app.include_router(
    questions.router,
    tags=["questions"]
)
app.include_router(
    quizzes.router,
    tags=["quizzes"]
)
app.include_router(
    categories.router,
    tags=["categories"]
)
app.include_router(
    users.router,
    prefix="/api",
    tags=["users"]
)

@app.get("/", tags=["root"])
async def root(settings: Settings = Depends(get_settings)):
    """Root endpoint with API information"""
    return {
        "app_name": settings.APP_NAME,
        "version": "2.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

if __name__ == '__main__':
    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=9000,
        reload=True,
        log_level="info"
    )