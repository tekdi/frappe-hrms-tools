"""
CV Analysis API Endpoints
"""
import logging
import json
import base64
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional

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


@router.post(
    "/analyze-upload",
    response_model=CVAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a CV (Multipart Upload)",
    description="Analyze a CV using multipart file upload - more efficient than base64",
    responses={
        200: {"description": "Analysis completed successfully"},
        400: {"description": "Invalid request", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
async def analyze_cv_upload(
    cv_file: UploadFile = File(..., description="CV file (PDF or DOCX)"),
    position_framework: str = Form(..., description="JSON string of position framework"),
    company_criteria: str = Form(..., description="JSON string of company criteria"),
    llm_provider: str = Form(default="auto", description="LLM provider to use"),
    prompt_version: str = Form(default="v1", description="Prompt version"),
    analysis_depth: str = Form(default="detailed", description="Analysis depth (quick/detailed)")
):
    """
    Analyze a CV using multipart file upload (recommended for large files)

    This endpoint is more efficient than the base64 endpoint:
    - No base64 encoding overhead (~33% size reduction)
    - Better memory efficiency
    - Standard HTTP file upload

    **Form Fields:**
    - `cv_file`: The CV file (multipart upload)
    - `position_framework`: JSON string of position requirements
    - `company_criteria`: JSON string of company criteria
    - `llm_provider`: LLM provider (openai/anthropic/gemini/auto)
    - `prompt_version`: Version of prompt to use
    - `analysis_depth`: Level of detail (quick/detailed)

    **Example using curl:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/analyze-upload \\
      -F "cv_file=@/path/to/cv.pdf" \\
      -F "position_framework={...json...}" \\
      -F "company_criteria={...json...}" \\
      -F "llm_provider=auto"
    ```
    """
    try:
        logger.info(f"Received upload analysis request for: {cv_file.filename}")

        # Validate file type
        if not cv_file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "ValidationError", "message": "Filename is required"}
            )

        allowed_extensions = ['.pdf', '.doc', '.docx']
        if not any(cv_file.filename.lower().endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "ValidationError",
                    "message": f"File must be one of: {', '.join(allowed_extensions)}"
                }
            )

        # Read file content and encode to base64 (for internal processing)
        file_content = await cv_file.read()
        cv_base64 = base64.b64encode(file_content).decode()

        # Parse JSON strings
        try:
            position_framework_dict = json.loads(position_framework)
            company_criteria_dict = json.loads(company_criteria)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "ValidationError",
                    "message": f"Invalid JSON in form fields: {str(e)}"
                }
            )

        # Build request object
        request = CVAnalysisRequest(
            cv_file=cv_base64,
            cv_filename=cv_file.filename,
            position_framework=position_framework_dict,
            company_criteria=company_criteria_dict,
            config={
                "llm_provider": llm_provider,
                "prompt_version": prompt_version,
                "analysis_depth": analysis_depth
            }
        )

        # Perform analysis
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

    except HTTPException:
        raise  # Re-raise HTTPException as-is

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
