# Copyright (c) 2025, TEKDI and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PositionEvaluationFramework(Document):
	"""Position Evaluation Framework DocType"""

	def validate(self):
		"""Validate that weights add up to 100"""
		total_weight = (
			(self.technical_skills_weight or 0) +
			(self.experience_weight or 0) +
			(self.education_weight or 0) +
			(self.cultural_fit_weight or 0)
		)

		if total_weight != 100:
			frappe.msgprint(
				f"Warning: Scoring weights should add up to 100%. Current total: {total_weight}%",
				indicator="orange"
			)

	def get_framework_dict(self):
		"""Convert framework to dictionary format for API"""
		return {
			"role_title": self.role_title or "",
			"key_requirements": [r.strip() for r in (self.key_requirements or "").split('\n') if r.strip()],
			"scoring_weights": {
				"technical_skills": self.technical_skills_weight or 40,
				"experience": self.experience_weight or 30,
				"education": self.education_weight or 15,
				"cultural_fit": self.cultural_fit_weight or 15
			},
			"must_have_skills": [s.strip() for s in (self.must_have_skills or "").split('\n') if s.strip()],
			"nice_to_have_skills": [s.strip() for s in (self.nice_to_have_skills or "").split('\n') if s.strip()],
			"experience_years_required": self.experience_years_required or 0
		}
