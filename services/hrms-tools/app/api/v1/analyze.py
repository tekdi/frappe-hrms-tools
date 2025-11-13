"""
CV Analysis API Endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.request import CVAnalysisRequest
from app.models.response import CVAnalysisResponse, ErrorResponse, HealthResponse
from app.services.cv_analyzer import get_cv_analyzer, CVAnalyzerError
from app.core.config import get_settings
from app.core.llm_factory import get_llm_factory

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=CVAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a CV",
    description="Analyze a CV against position and company criteria using AI",
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
async def analyze_cv(request: CVAnalysisRequest):
    """
    Analyze a CV and return structured evaluation results

    This endpoint:
    1. Parses the CV document (PDF/DOCX)
    2. Evaluates against position requirements
    3. Applies company-wide criteria
    4. Returns detailed scores, strengths, gaps, and interview questions

    **Request Body:**
    - `cv_file`: Base64 encoded CV file
    - `cv_filename`: Original filename
    - `position_framework`: Position-specific requirements and scoring weights
    - `company_criteria`: Company-wide evaluation standards
    - `config`: Analysis configuration (LLM provider, prompt version, etc.)

    **Response:**
    - Structured analysis with scores, recommendations, and insights
    """
    try:
        logger.info(f"Received analysis request for: {request.cv_filename}")

        # Get analyzer and perform analysis
        analyzer = get_cv_analyzer()
        response = await analyzer.analyze(request)

        return response

    except CVAnalyzerError as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "AnalysisError",
                "message": str(e)
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "An unexpected error occurred during analysis"
            }
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check service health and available LLM providers"
)
async def health_check():
    """
    Health check endpoint

    Returns:
    - Service status
    - Version information
    - Available LLM providers
    """
    settings = get_settings()
    llm_factory = get_llm_factory()

    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        llm_providers=llm_factory.get_available_providers()
    )


@router.get(
    "/",
    summary="API Info",
    description="Get API information"
)
async def api_info():
    """
    Get API information
    """
    settings = get_settings()

    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "endpoints": {
            "analyze": f"{settings.API_V1_PREFIX}/analyze",
            "health": f"{settings.API_V1_PREFIX}/health"
        },
        "documentation": "/docs"
    }
