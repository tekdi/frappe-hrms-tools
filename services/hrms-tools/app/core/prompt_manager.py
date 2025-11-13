"""
Prompt Management System
Handles versioned prompts for CV analysis
"""
import os
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages versioned prompts for CV analysis"""

    def __init__(self, prompts_dir: str = "app/prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._prompts_cache: Dict[str, str] = {}
        self._load_prompts()

    def _load_prompts(self):
        """Load all prompt templates from the prompts directory"""
        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory not found: {self.prompts_dir}")
            return

        for prompt_file in self.prompts_dir.glob("*.txt"):
            version = prompt_file.stem  # e.g., "v1_analysis" -> "v1_analysis"
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    self._prompts_cache[version] = f.read()
                logger.info(f"Loaded prompt template: {version}")
            except Exception as e:
                logger.error(f"Failed to load prompt {version}: {e}")

    def get_prompt(self, version: str = "v1") -> str:
        """
        Get a prompt template by version

        Args:
            version: Prompt version (e.g., "v1", "v2")

        Returns:
            Prompt template string

        Raises:
            ValueError: If prompt version not found
        """
        prompt_key = f"{version}_analysis"

        if prompt_key not in self._prompts_cache:
            # Try exact match
            if version in self._prompts_cache:
                prompt_key = version
            else:
                available = list(self._prompts_cache.keys())
                raise ValueError(
                    f"Prompt version '{version}' not found. Available versions: {available}"
                )

        return self._prompts_cache[prompt_key]

    def build_analysis_prompt(
        self,
        cv_text: str,
        position_framework: dict,
        company_criteria: dict,
        analysis_depth: str = "detailed"
    ) -> tuple[str, str]:
        """
        Build a complete analysis prompt from template and data

        Args:
            cv_text: Extracted CV text
            position_framework: Position-specific requirements
            company_criteria: Company-wide evaluation criteria
            analysis_depth: Level of analysis detail

        Returns:
            Tuple of (system_prompt, user_prompt)
        """

        # Build position requirements section
        requirements_text = "\n".join([
            f"- {req}" for req in position_framework.get('key_requirements', [])
        ])

        must_have = ", ".join(position_framework.get('must_have_skills', []))
        nice_to_have = ", ".join(position_framework.get('nice_to_have_skills', []))

        # Build company values section
        values_text = ", ".join(company_criteria.get('values', []))

        # Build scoring weights
        weights = position_framework.get('scoring_weights', {})
        weights_text = "\n".join([
            f"- {section.replace('_', ' ').title()}: {weight}%"
            for section, weight in weights.items()
        ])

        # System prompt
        system_prompt = """You are an expert HR analyst specializing in candidate evaluation.
Your task is to analyze CVs objectively and provide structured, data-driven assessments.

IMPORTANT: You must respond with valid JSON only. Do not include any text outside the JSON structure.

The JSON response must have this exact structure:
{
  "overall_score": <number 0-100>,
  "recommendation": "<strong_yes|yes|maybe|no|strong_no>",
  "section_scores": [
    {
      "section": "<section name>",
      "score": <number 0-100>,
      "weight": <number 0-100>,
      "weighted_score": <calculated: score * weight / 100>,
      "rationale": "<detailed explanation>"
    }
  ],
  "key_strengths": ["<strength 1>", "<strength 2>", ...],
  "critical_gaps": ["<gap 1>", "<gap 2>", ...],
  "follow_up_questions": ["<question 1>", "<question 2>", ...]
}

Be objective, thorough, and ensure all scores are justified with clear rationale."""

        # User prompt
        user_prompt = f"""Analyze the following CV against the position requirements and company criteria.

=== POSITION INFORMATION ===
Role: {position_framework.get('role_title', 'Not specified')}

Key Requirements:
{requirements_text if requirements_text else 'Not specified'}

Must-Have Skills: {must_have if must_have else 'Not specified'}
Nice-to-Have Skills: {nice_to_have if nice_to_have else 'Not specified'}

Scoring Weights:
{weights_text}

=== COMPANY CRITERIA ===
Company: {company_criteria.get('company_name', 'Not specified')}
Core Values: {values_text if values_text else 'Not specified'}

Evaluation Guidelines:
{company_criteria.get('evaluation_guidelines', 'Not specified')}

Disqualifiers:
{', '.join(company_criteria.get('disqualifiers', [])) if company_criteria.get('disqualifiers') else 'None specified'}

=== CANDIDATE CV ===
{cv_text}

=== ANALYSIS INSTRUCTIONS ===
1. Evaluate the candidate across all scoring dimensions (Technical Skills, Experience, Education, Cultural Fit)
2. Calculate weighted scores based on the provided weights
3. Identify 3-5 key strengths with specific evidence from the CV
4. Identify 2-4 critical gaps or concerns
5. Generate 4-6 thoughtful follow-up interview questions
6. Provide an overall recommendation (strong_yes, yes, maybe, no, or strong_no)

Analysis Depth: {analysis_depth}

Respond with ONLY the JSON structure specified in the system prompt."""

        return system_prompt, user_prompt

    def get_available_versions(self) -> list:
        """Get list of available prompt versions"""
        return list(self._prompts_cache.keys())


# Global prompt manager instance
_prompt_manager_instance: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get or create the global prompt manager instance"""
    global _prompt_manager_instance
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptManager()
    return _prompt_manager_instance
