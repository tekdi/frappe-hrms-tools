# Copyright (c) 2025, TEKDI and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CompanyEvaluationCriteria(Document):
	"""Company Evaluation Criteria DocType"""

	def get_criteria_dict(self):
		"""Convert criteria to dictionary format for API"""
		return {
			"company_name": self.company_name or "",
			"values": [v.strip() for v in (self.company_values or "").split('\n') if v.strip()],
			"evaluation_guidelines": self.evaluation_guidelines or "",
			"disqualifiers": [d.strip() for d in (self.disqualifiers or "").split('\n') if d.strip()],
			"preferred_backgrounds": [p.strip() for p in (self.preferred_backgrounds or "").split('\n') if p.strip()]
		}
