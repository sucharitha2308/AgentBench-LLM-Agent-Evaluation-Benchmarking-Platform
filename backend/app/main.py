from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.logging import setup_logging, logger
from app.core.errors import AgentBenchException, agentbench_exception_handler
from app.database.session import SessionLocal
from app.database.init_db import init_db
from app.api.v1.api import api_router
from app.api.v1.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    setup_logging()
    logger.info("Initializing AgentBench platform...")
    db = SessionLocal()
    try:
        init_db(db)
        logger.info("AgentBench database initialized and seeded successfully.")
    except Exception as e:
        logger.exception(f"Database initialization error: {e}")
    finally:
        db.close()
    yield
    # Shutdown actions
    logger.info("AgentBench platform shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="AgentBench – LLM Agent Evaluation, Benchmarking & Observability Platform",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AgentBenchException, agentbench_exception_handler)

# Health routes at root level
app.include_router(health_router)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": "AgentBench API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "online"
    }
