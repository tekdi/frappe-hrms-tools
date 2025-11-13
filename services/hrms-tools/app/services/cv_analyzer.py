"""
CV Analyzer Service
Main orchestrator for CV analysis workflow
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any
import time

from app.models.request import CVAnalysisRequest
from app.models.response import (
    CVAnalysisResponse,
    SectionScore,
    AnalysisMetadata,
    RecommendationType
)
from app.services.document_parser import get_document_parser, DocumentParserError
from app.core.llm_factory import get_llm_factory
from app.core.prompt_manager import get_prompt_manager
from app.services.audit_logger import get_audit_logger
from app.llm_providers.base import LLMProviderError

logger = logging.getLogger(__name__)


class CVAnalyzerError(Exception):
    """Exception raised when CV analysis fails"""
    pass


class CVAnalyzer:
    """Main service for analyzing CVs"""

    def __init__(self):
        self.document_parser = get_document_parser()
        self.llm_factory = get_llm_factory()
        self.prompt_manager = get_prompt_manager()
        self.audit_logger = get_audit_logger()

    async def analyze(self, request: CVAnalysisRequest) -> CVAnalysisResponse:
        """
        Perform complete CV analysis

        Args:
            request: CV analysis request with all required data

        Returns:
            CVAnalysisResponse with structured analysis results

        Raises:
            CVAnalyzerError: If analysis fails at any step
        """
        analysis_id = str(uuid.uuid4())
        start_time = time.time()

        logger.info(f"Starting CV analysis {analysis_id} for {request.cv_filename}")

        try:
            # Step 1: Parse CV document
            cv_text, page_count = self._parse_document(request)

            # Step 2: Get LLM provider
            llm_provider = self.llm_factory.get_provider(request.config.llm_provider)

            # Step 3: Build analysis prompt
            system_prompt, user_prompt = self._build_prompt(request, cv_text)

            # Step 4: Call LLM for analysis
            llm_response = await llm_provider.generate(user_prompt, system_prompt)

            # Step 5: Parse LLM response into structured format
            analysis_result = self._parse_llm_response(llm_response.content)

            # Step 6: Build response
            processing_time_ms = int((time.time() - start_time) * 1000)

            response = self._build_response(
                analysis_id=analysis_id,
                analysis_result=analysis_result,
                llm_provider=llm_provider.get_provider_name(),
                llm_model=llm_response.model,
                prompt_version=request.config.prompt_version,
                tokens_used=llm_response.tokens_used,
                processing_time_ms=processing_time_ms,
                page_count=page_count
            )

            # Step 7: Audit log
            self._log_analysis(
                analysis_id=analysis_id,
                request=request,
                response=response,
                processing_time_ms=processing_time_ms,
                status="success"
            )

            logger.info(f"Analysis {analysis_id} completed successfully in {processing_time_ms}ms")
            return response

        except DocumentParserError as e:
            logger.error(f"Document parsing failed: {e}")
            self._log_analysis(
                analysis_id=analysis_id,
                request=request,
                response=None,
                processing_time_ms=int((time.time() - start_time) * 1000),
                status="error",
                error_message=str(e)
            )
            raise CVAnalyzerError(f"Failed to parse CV document: {str(e)}")

        except LLMProviderError as e:
            logger.error(f"LLM provider error: {e}")
            self._log_analysis(
                analysis_id=analysis_id,
                request=request,
                response=None,
                processing_time_ms=int((time.time() - start_time) * 1000),
                status="error",
                error_message=str(e)
            )
            raise CVAnalyzerError(f"LLM analysis failed: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
            self._log_analysis(
                analysis_id=analysis_id,
                request=request,
                response=None,
                processing_time_ms=int((time.time() - start_time) * 1000),
                status="error",
                error_message=str(e)
            )
            raise CVAnalyzerError(f"Analysis failed: {str(e)}")

    def _parse_document(self, request: CVAnalysisRequest) -> tuple[str, int]:
        """
        Parse CV document and extract text

        Args:
            request: Analysis request

        Returns:
            Tuple of (extracted_text, page_count)
        """
        logger.info(f"Parsing document: {request.cv_filename}")

        cv_text, page_count = self.document_parser.parse_base64(
            request.cv_file,
            request.cv_filename
        )

        logger.info(f"Extracted {len(cv_text)} characters from {page_count} pages")
        return cv_text, page_count

    def _build_prompt(self, request: CVAnalysisRequest, cv_text: str) -> tuple[str, str]:
        """
        Build analysis prompt from template and request data

        Args:
            request: Analysis request
            cv_text: Extracted CV text

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        logger.info(f"Building prompt using version: {request.config.prompt_version}")

        system_prompt, user_prompt = self.prompt_manager.build_analysis_prompt(
            cv_text=cv_text,
            position_framework=request.position_framework.model_dump(),
            company_criteria=request.company_criteria.model_dump(),
            analysis_depth=request.config.analysis_depth
        )

        return system_prompt, user_prompt

    def _parse_llm_response(self, llm_content: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured format

        Args:
            llm_content: Raw LLM response (should be JSON)

        Returns:
            Parsed dict

        Raises:
            CVAnalyzerError: If parsing fails
        """
        try:
            # Clean the content - some LLMs wrap JSON in markdown code blocks
            cleaned_content = llm_content.strip()

            # Remove markdown code block markers if present
            if cleaned_content.startswith('```'):
                # Find the first newline after opening ```
                first_newline = cleaned_content.find('\n')
                if first_newline != -1:
                    # Remove opening ``` and language identifier
                    cleaned_content = cleaned_content[first_newline + 1:]

                # Remove closing ```
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3].rstrip()

            # Try to parse as JSON
            result = json.loads(cleaned_content)

            # Validate required fields
            required_fields = [
                'overall_score', 'recommendation', 'section_scores',
                'key_strengths', 'critical_gaps', 'follow_up_questions'
            ]

            for field in required_fields:
                if field not in result:
                    raise CVAnalyzerError(f"Missing required field in LLM response: {field}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"LLM response content (first 500 chars): {llm_content[:500]}...")
            logger.error(f"Cleaned content (first 500 chars): {cleaned_content[:500] if 'cleaned_content' in locals() else 'N/A'}...")
            raise CVAnalyzerError("LLM did not return valid JSON. Please try again.")

    def _build_response(
        self,
        analysis_id: str,
        analysis_result: Dict[str, Any],
        llm_provider: str,
        llm_model: str,
        prompt_version: str,
        tokens_used: int,
        processing_time_ms: int,
        page_count: int
    ) -> CVAnalysisResponse:
        """
        Build CVAnalysisResponse from parsed LLM result

        Args:
            analysis_id: Unique analysis ID
            analysis_result: Parsed LLM response
            llm_provider: Provider name
            llm_model: Model name
            prompt_version: Prompt version used
            tokens_used: Tokens consumed
            processing_time_ms: Processing time
            page_count: Number of CV pages

        Returns:
            CVAnalysisResponse
        """
        # Parse section scores
        section_scores = [
            SectionScore(**section)
            for section in analysis_result['section_scores']
        ]

        # Build metadata
        metadata = AnalysisMetadata(
            llm_provider=llm_provider,
            model=llm_model,
            prompt_version=prompt_version,
            tokens_used=tokens_used,
            processing_time_ms=processing_time_ms,
            cv_pages=page_count
        )

        # Build response
        response = CVAnalysisResponse(
            analysis_id=analysis_id,
            timestamp=datetime.utcnow(),
            overall_score=analysis_result['overall_score'],
            recommendation=RecommendationType(analysis_result['recommendation']),
            section_scores=section_scores,
            key_strengths=analysis_result['key_strengths'],
            critical_gaps=analysis_result['critical_gaps'],
            follow_up_questions=analysis_result['follow_up_questions'],
            metadata=metadata
        )

        return response

    def _log_analysis(
        self,
        analysis_id: str,
        request: CVAnalysisRequest,
        response: CVAnalysisResponse | None,
        processing_time_ms: int,
        status: str,
        error_message: str | None = None
    ):
        """
        Log analysis to audit database

        Args:
            analysis_id: Analysis ID
            request: Original request
            response: Analysis response (None if failed)
            processing_time_ms: Processing time
            status: Status (success/error)
            error_message: Error message if failed
        """
        try:
            self.audit_logger.log_analysis(
                analysis_id=analysis_id,
                cv_filename=request.cv_filename,
                position_title=request.position_framework.role_title,
                company_name=request.company_criteria.company_name,
                llm_provider=request.config.llm_provider,
                llm_model=response.metadata.model if response else "unknown",
                prompt_version=request.config.prompt_version,
                tokens_used=response.metadata.tokens_used if response else None,
                processing_time_ms=processing_time_ms,
                overall_score=response.overall_score if response else None,
                recommendation=response.recommendation.value if response else None,
                status=status,
                error_message=error_message
            )
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")


# Global analyzer instance
_analyzer_instance = None


def get_cv_analyzer() -> CVAnalyzer:
    """Get or create the global CV analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = CVAnalyzer()
    return _analyzer_instance
