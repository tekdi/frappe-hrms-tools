"""
Response models for CV Analysis API
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class RecommendationType(str, Enum):
    """Recommendation types for candidates"""
    STRONG_YES = "strong_yes"
    YES = "yes"
    MAYBE = "maybe"
    NO = "no"
    STRONG_NO = "strong_no"


class SectionScore(BaseModel):
    """Score for a specific evaluation section"""
    section: str = Field(..., description="Section name (e.g., Technical Skills)")
    score: float = Field(..., ge=0, le=100, description="Raw score for this section (0-100)")
    weight: float = Field(..., ge=0, le=100, description="Weight of this section in overall score")
    weighted_score: float = Field(..., description="score * weight / 100")
    rationale: str = Field(..., description="Explanation for this section's score")

    class Config:
        json_schema_extra = {
            "example": {
                "section": "Technical Skills",
                "score": 85,
                "weight": 40,
                "weighted_score": 34.0,
                "rationale": "Strong Python background with 7 years experience. Demonstrated microservices expertise."
            }
        }


class AnalysisMetadata(BaseModel):
    """Metadata about the analysis process"""
    llm_provider: str = Field(..., description="LLM provider used")
    model: str = Field(..., description="Specific model used")
    prompt_version: str = Field(..., description="Version of the prompt template")
    tokens_used: Optional[int] = Field(None, description="Number of tokens consumed")
    processing_time_ms: int = Field(..., description="Time taken to process in milliseconds")
    cv_pages: Optional[int] = Field(None, description="Number of pages in the CV")

    class Config:
        json_schema_extra = {
            "example": {
                "llm_provider": "openai",
                "model": "gpt-4-turbo-preview",
                "prompt_version": "v1",
                "tokens_used": 3450,
                "processing_time_ms": 2340,
                "cv_pages": 2
            }
        }


class CVAnalysisResponse(BaseModel):
    """Main response model for CV analysis"""
    analysis_id: str = Field(..., description="Unique identifier for this analysis")
    timestamp: datetime = Field(..., description="When the analysis was completed")
    overall_score: float = Field(..., ge=0, le=100, description="Overall candidate score (0-100)")
    recommendation: RecommendationType = Field(..., description="Hiring recommendation")

    section_scores: List[SectionScore] = Field(..., description="Detailed scores by section")
    key_strengths: List[str] = Field(..., description="Candidate's key strengths")
    critical_gaps: List[str] = Field(..., description="Critical gaps or concerns")
    follow_up_questions: List[str] = Field(..., description="Suggested interview questions")

    metadata: AnalysisMetadata = Field(..., description="Analysis metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-11-13T10:30:00Z",
                "overall_score": 78,
                "recommendation": "strong_yes",
                "section_scores": [
                    {
                        "section": "Technical Skills",
                        "score": 85,
                        "weight": 40,
                        "weighted_score": 34.0,
                        "rationale": "Strong Python background with demonstrated expertise"
                    }
                ],
                "key_strengths": [
                    "7 years of Python development",
                    "Proven microservices expertise"
                ],
                "critical_gaps": [
                    "No Kubernetes experience mentioned"
                ],
                "follow_up_questions": [
                    "Can you describe your experience with event-driven architectures?"
                ],
                "metadata": {
                    "llm_provider": "openai",
                    "model": "gpt-4-turbo-preview",
                    "prompt_version": "v1",
                    "tokens_used": 3450,
                    "processing_time_ms": 2340,
                    "cv_pages": 2
                }
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Detailed error message")
    details: Optional[dict] = Field(None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid CV file format",
                "details": {"filename": "invalid.txt"}
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    llm_providers: dict = Field(..., description="Available LLM providers and their status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "llm_providers": {
                    "openai": "available",
                    "anthropic": "available",
                    "gemini": "not_configured"
                }
            }
        }
