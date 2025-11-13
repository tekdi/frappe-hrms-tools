# Copyright (c) 2025, TEKDI and contributors
# For license information, please see license.txt

"""
API Client for CV Analysis Microservice
"""

import frappe
import requests
import base64
from frappe import _


class CVAnalysisClient:
	"""Client for interacting with CV Analysis microservice"""

	def __init__(self):
		"""Initialize client with settings"""
		self.settings = frappe.get_single("CV Analysis Settings")

	def check_health(self):
		"""
		Check if the CV Analysis service is healthy

		Returns:
			dict: Health check response
		"""
		try:
			url = self.settings.get_health_url()
			response = requests.get(url, timeout=10)
			response.raise_for_status()
			return response.json()
		except requests.exceptions.RequestException as e:
			frappe.log_error(
				title="CV Analysis Service Health Check Failed",
				message=str(e)
			)
			return None

	def analyze_cv(self, job_applicant_doc, cv_file_url):
		"""
		Analyze a CV using the microservice

		Args:
			job_applicant_doc: Job Applicant document
			cv_file_url: URL or path to CV file in Frappe

		Returns:
			dict: Analysis response from microservice

		Raises:
			frappe.ValidationError: If analysis fails
		"""
		# Get CV file content
		cv_base64 = self._get_cv_base64(cv_file_url)
		if not cv_base64:
			frappe.throw(_("Could not read CV file"))

		# Get evaluation frameworks
		position_framework = self._get_position_framework(job_applicant_doc.job_title)
		company_criteria = self._get_company_criteria()

		# Build request payload
		payload = {
			"cv_file": cv_base64,
			"cv_filename": self._get_filename_from_url(cv_file_url),
			"position_framework": position_framework,
			"company_criteria": company_criteria,
			"config": {
				"llm_provider": self.settings.default_llm_provider or "auto",
				"prompt_version": self.settings.default_prompt_version or "v1",
				"analysis_depth": "detailed"
			}
		}

		# Call microservice
		try:
			url = self.settings.get_api_url()
			frappe.publish_realtime(
				event="cv_analysis_progress",
				message={"status": "started", "applicant": job_applicant_doc.name},
				user=frappe.session.user
			)

			response = requests.post(url, json=payload, timeout=120)
			response.raise_for_status()

			result = response.json()

			frappe.publish_realtime(
				event="cv_analysis_progress",
				message={"status": "completed", "applicant": job_applicant_doc.name},
				user=frappe.session.user
			)

			return result

		except requests.exceptions.Timeout:
			frappe.log_error(
				title="CV Analysis Timeout",
				message=f"Analysis timed out for {job_applicant_doc.name}"
			)
			frappe.throw(_("CV analysis timed out. Please try again later."))

		except requests.exceptions.RequestException as e:
			error_msg = str(e)
			if hasattr(e, 'response') and e.response is not None:
				try:
					error_detail = e.response.json()
					error_msg = error_detail.get('message', error_msg)
				except:
					pass

			frappe.log_error(
				title="CV Analysis API Error",
				message=f"Error analyzing CV for {job_applicant_doc.name}: {error_msg}"
			)
			frappe.throw(_("CV analysis failed: {0}").format(error_msg))

	def _get_cv_base64(self, file_url):
		"""
		Get base64 encoded CV file

		Args:
			file_url: Frappe file URL

		Returns:
			str: Base64 encoded file content
		"""
		try:
			# Get file doc
			file_doc = frappe.get_doc("File", {"file_url": file_url})

			# Read file content
			if file_doc.is_private:
				file_path = frappe.get_site_path("private", "files", file_doc.file_name)
			else:
				file_path = frappe.get_site_path("public", "files", file_doc.file_name)

			with open(file_path, "rb") as f:
				content = f.read()

			return base64.b64encode(content).decode()

		except Exception as e:
			frappe.log_error(
				title="Error Reading CV File",
				message=str(e)
			)
			return None

	def _get_filename_from_url(self, file_url):
		"""Extract filename from file URL"""
		if not file_url:
			return "cv.pdf"

		# Get filename from URL
		parts = file_url.split('/')
		return parts[-1] if parts else "cv.pdf"

	def _get_position_framework(self, job_title):
		"""
		Get position evaluation framework

		Args:
			job_title: Job Opening name

		Returns:
			dict: Position framework
		"""
		if not job_title:
			# Return default framework
			return {
				"role_title": "General Position",
				"key_requirements": [],
				"scoring_weights": {
					"technical_skills": 40,
					"experience": 30,
					"education": 15,
					"cultural_fit": 15
				},
				"must_have_skills": [],
				"nice_to_have_skills": [],
				"experience_years_required": 0
			}

		# Try to find position framework
		if frappe.db.exists("Position Evaluation Framework", job_title):
			framework_doc = frappe.get_doc("Position Evaluation Framework", job_title)
			return framework_doc.get_framework_dict()

		# Fallback: create basic framework from job opening
		if frappe.db.exists("Job Opening", job_title):
			job_opening = frappe.get_doc("Job Opening", job_title)
			return {
				"role_title": job_opening.job_title or job_title,
				"key_requirements": [job_opening.description[:200]] if job_opening.description else [],
				"scoring_weights": {
					"technical_skills": 40,
					"experience": 30,
					"education": 15,
					"cultural_fit": 15
				},
				"must_have_skills": [],
				"nice_to_have_skills": [],
				"experience_years_required": 0
			}

		# Default framework
		return {
			"role_title": job_title,
			"key_requirements": [],
			"scoring_weights": {
				"technical_skills": 40,
				"experience": 30,
				"education": 15,
				"cultural_fit": 15
			},
			"must_have_skills": [],
			"nice_to_have_skills": [],
			"experience_years_required": 0
		}

	def _get_company_criteria(self):
		"""
		Get company evaluation criteria

		Returns:
			dict: Company criteria
		"""
		if frappe.db.exists("Company Evaluation Criteria", "Company Evaluation Criteria"):
			criteria_doc = frappe.get_single("Company Evaluation Criteria")
			return criteria_doc.get_criteria_dict()

		# Default criteria
		return {
			"company_name": frappe.defaults.get_defaults().get("company") or "Company",
			"values": [],
			"evaluation_guidelines": "",
			"disqualifiers": [],
			"preferred_backgrounds": []
		}


def get_client():
	"""Get CV Analysis Client instance"""
	return CVAnalysisClient()
