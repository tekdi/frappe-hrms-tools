"""
Request models for CV Analysis API
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List
import base64


class ScoringWeights(BaseModel):
    """Scoring weights for different evaluation sections"""
    technical_skills: int = Field(default=40, ge=0, le=100)
    experience: int = Field(default=30, ge=0, le=100)
    education: int = Field(default=15, ge=0, le=100)
    cultural_fit: int = Field(default=15, ge=0, le=100)

    @field_validator('technical_skills', 'experience', 'education', 'cultural_fit')
    @classmethod
    def validate_weights(cls, v):
        """Ensure weights are valid percentages"""
        if not 0 <= v <= 100:
            raise ValueError("Weight must be between 0 and 100")
        return v


class PositionFramework(BaseModel):
    """Position-specific evaluation framework"""
    role_title: str = Field(..., min_length=1, description="Job title/role")
    key_requirements: List[str] = Field(default_factory=list, description="Key requirements for the role")
    scoring_weights: ScoringWeights = Field(default_factory=ScoringWeights)
    must_have_skills: List[str] = Field(default_factory=list, description="Essential skills")
    nice_to_have_skills: List[str] = Field(default_factory=list, description="Preferred but not essential skills")
    experience_years_required: Optional[int] = Field(default=None, ge=0, description="Minimum years of experience")


class CompanyCriteria(BaseModel):
    """Company-wide evaluation criteria"""
    company_name: str = Field(..., min_length=1)
    values: List[str] = Field(default_factory=list, description="Company core values")
    evaluation_guidelines: str = Field(default="", description="General evaluation guidelines")
    disqualifiers: List[str] = Field(default_factory=list, description="Automatic disqualification criteria")
    preferred_backgrounds: List[str] = Field(default_factory=list, description="Preferred educational or professional backgrounds")


class AnalysisConfig(BaseModel):
    """Configuration for the analysis process"""
    llm_provider: str = Field(default="auto", description="LLM provider: openai, anthropic, gemini, or auto")
    prompt_version: str = Field(default="v1", description="Version of the analysis prompt to use")
    analysis_depth: str = Field(default="detailed", description="Analysis depth: quick or detailed")

    @field_validator('llm_provider')
    @classmethod
    def validate_provider(cls, v):
        """Validate LLM provider"""
        allowed = ['openai', 'anthropic', 'gemini', 'auto']
        if v.lower() not in allowed:
            raise ValueError(f"LLM provider must be one of {allowed}")
        return v.lower()

    @field_validator('analysis_depth')
    @classmethod
    def validate_depth(cls, v):
        """Validate analysis depth"""
        allowed = ['quick', 'detailed']
        if v.lower() not in allowed:
            raise ValueError(f"Analysis depth must be one of {allowed}")
        return v.lower()


class CVAnalysisRequest(BaseModel):
    """Main request model for CV analysis"""
    cv_file: str = Field(..., description="Base64 encoded CV file or URL to file")
    cv_filename: str = Field(..., min_length=1, description="Original filename of the CV")
    position_framework: PositionFramework = Field(..., description="Position-specific evaluation criteria")
    company_criteria: CompanyCriteria = Field(..., description="Company-wide evaluation criteria")
    config: AnalysisConfig = Field(default_factory=AnalysisConfig, description="Analysis configuration")

    @field_validator('cv_file')
    @classmethod
    def validate_cv_file(cls, v):
        """Validate that cv_file is valid base64 or URL"""
        if v.startswith('http://') or v.startswith('https://'):
            # It's a URL
            return v

        # Try to validate as base64
        try:
            # Try to decode to verify it's valid base64
            base64.b64decode(v, validate=True)
            return v
        except Exception:
            raise ValueError("cv_file must be either a valid URL or base64 encoded string")

    @field_validator('cv_filename')
    @classmethod
    def validate_filename(cls, v):
        """Validate file extension"""
        allowed_extensions = ['.pdf', '.doc', '.docx']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f"File must have one of these extensions: {allowed_extensions}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "cv_file": "JVBERi0xLjQKJeLjz9MKM...",
                "cv_filename": "john_doe_cv.pdf",
                "position_framework": {
                    "role_title": "Senior Backend Engineer",
                    "key_requirements": [
                        "5+ years Python experience",
                        "Microservices architecture",
                        "Database design"
                    ],
                    "scoring_weights": {
                        "technical_skills": 40,
                        "experience": 30,
                        "education": 15,
                        "cultural_fit": 15
                    },
                    "must_have_skills": ["Python", "REST API"],
                    "nice_to_have_skills": ["Docker", "Kubernetes"]
                },
                "company_criteria": {
                    "company_name": "ACME Corp",
                    "values": ["Innovation", "Collaboration", "Ownership"],
                    "evaluation_guidelines": "Focus on problem-solving ability and cultural alignment",
                    "disqualifiers": ["Less than 3 years experience"]
                },
                "config": {
                    "llm_provider": "openai",
                    "prompt_version": "v1",
                    "analysis_depth": "detailed"
                }
            }
        }
