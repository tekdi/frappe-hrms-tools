# Copyright (c) 2025, TEKDI and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CVAnalysisResult(Document):
	"""CV Analysis Result DocType"""

	def before_save(self):
		"""Set read-only fields if not set"""
		if not self.analysis_date:
			self.analysis_date = frappe.utils.now()

	@staticmethod
	def create_from_api_response(job_applicant, api_response):
		"""
		Create a CV Analysis Result from API response

		Args:
			job_applicant: Job Applicant docname
			api_response: Dict containing API response

		Returns:
			CV Analysis Result document
		"""
		doc = frappe.get_doc({
			"doctype": "CV Analysis Result",
			"job_applicant": job_applicant,
			"analysis_id": api_response.get("analysis_id"),
			"overall_score": api_response.get("overall_score"),
			"recommendation": api_response.get("recommendation"),
			"llm_provider": api_response.get("metadata", {}).get("llm_provider"),
			"tokens_used": api_response.get("metadata", {}).get("tokens_used"),
			"processing_time_ms": api_response.get("metadata", {}).get("processing_time_ms")
		})

		# Add section scores
		for section in api_response.get("section_scores", []):
			doc.append("section_scores", {
				"section": section.get("section"),
				"score": section.get("score"),
				"weight": section.get("weight"),
				"weighted_score": section.get("weighted_score"),
				"rationale": section.get("rationale")
			})

		# Add strengths
		for strength in api_response.get("key_strengths", []):
			doc.append("insights", {
				"insight_type": "Strength",
				"description": strength
			})

		# Add gaps
		for gap in api_response.get("critical_gaps", []):
			doc.append("insights", {
				"insight_type": "Gap",
				"description": gap
			})

		# Add follow-up questions
		for question in api_response.get("follow_up_questions", []):
			doc.append("insights", {
				"insight_type": "Follow-up Question",
				"description": question
			})

		doc.insert(ignore_permissions=True)
		return doc
