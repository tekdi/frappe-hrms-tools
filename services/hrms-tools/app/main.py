"""
CV Analysis Service - Main Application
FastAPI application for analyzing candidate CVs
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.api.v1 import analyze
from app.core.llm_factory import get_llm_factory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler
    Handles startup and shutdown events
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize LLM factory to check provider availability
    llm_factory = get_llm_factory()
    available_providers = llm_factory.get_available_providers()

    logger.info("Available LLM providers:")
    for provider, status in available_providers.items():
        logger.info(f"  - {provider}: {status}")

    if not llm_factory.has_any_provider():
        logger.warning("⚠️  No LLM providers configured! Please set API keys in environment variables.")
    else:
        logger.info("✓ Service ready to accept requests")

    yield

    # Shutdown
    logger.info("Shutting down service")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    CV Analysis Service - AI-powered candidate evaluation system

    This service analyzes candidate CVs against position requirements and company criteria,
    providing structured evaluation results including:
    - Overall and section-wise scores
    - Key strengths identification
    - Critical gaps analysis
    - Suggested interview questions

    Supports multiple LLM providers: OpenAI, Anthropic Claude, and Google Gemini.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }
    )


# Include routers
app.include_router(
    analyze.router,
    prefix=settings.API_V1_PREFIX,
    tags=["analysis"]
)


# Root endpoint
@app.get("/", tags=["info"])
async def root():
    """Root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
