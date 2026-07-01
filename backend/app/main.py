from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from app.config import settings
from app.database import engine, Base, redis_client
from app.api import endpoints, sse

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запуск SPP Management приложения")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Таблицы созданы/проверены")
    yield
    logger.info("🛑 Остановка приложения")
    redis_client.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Система управления СПП",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix=settings.API_PREFIX)
app.include_router(sse.router, prefix=settings.API_PREFIX)

@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    })

@app.get("/")
async def root():
    return {
        "message": f"Добро пожаловать в {settings.PROJECT_NAME}!",
        "docs": "/docs",
        "health": "/health"
    }
