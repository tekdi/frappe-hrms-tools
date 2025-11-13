# Copyright (c) 2025, TEKDI and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CVAnalysisSettings(Document):
	"""CV Analysis Settings DocType"""

	def validate(self):
		"""Validate settings before save"""
		# Ensure service URL doesn't end with /
		if self.service_url and self.service_url.endswith('/'):
			self.service_url = self.service_url.rstrip('/')

	def get_api_url(self):
		"""Get the full API URL for CV analysis"""
		return f"{self.service_url}/api/{self.api_version}/analyze"

	def get_health_url(self):
		"""Get the health check URL"""
		return f"{self.service_url}/api/{self.api_version}/health"
