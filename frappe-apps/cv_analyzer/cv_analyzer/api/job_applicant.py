# Copyright (c) 2025, TEKDI and contributors
# For license information, please see license.txt

"""
Job Applicant hooks for CV Analysis
"""

import frappe
from frappe import _
from cv_analyzer.api.cv_analysis_client import get_client


def on_job_applicant_save(doc, method=None):
	"""
	Hook called when Job Applicant is saved
	Triggers CV analysis if resume is uploaded

	Args:
		doc: Job Applicant document
		method: Event method name
	"""
	# Check if auto-analysis is enabled
	settings = frappe.get_single("CV Analysis Settings")
	if not settings.auto_analyze_on_cv_upload:
		return

	# Check if resume attachment has changed
	if not doc.resume_attachment:
		return

	# Check if this is a new upload or update
	if method == "on_update":
		# Get the old doc to check if resume changed
		old_doc = doc.get_doc_before_save()
		if old_doc and old_doc.resume_attachment == doc.resume_attachment:
			# Resume hasn't changed, skip analysis
			return

	# Trigger CV analysis in background
	frappe.enqueue(
		analyze_cv_async,
		queue="long",
		timeout=300,
		job_applicant=doc.name,
		cv_file_url=doc.resume_attachment
	)

	frappe.msgprint(
		_("CV analysis has been queued. You will be notified when it's complete."),
		indicator="blue",
		alert=True
	)


def analyze_cv_async(job_applicant, cv_file_url):
	"""
	Analyze CV in background

	Args:
		job_applicant: Job Applicant docname
		cv_file_url: URL to CV file
	"""
	try:
		# Get job applicant doc
		doc = frappe.get_doc("Job Applicant", job_applicant)

		# Get client and analyze
		client = get_client()
		result = client.analyze_cv(doc, cv_file_url)

		# Save analysis result
		from cv_analyzer.cv_analyzer.doctype.cv_analysis_result.cv_analysis_result import CVAnalysisResult
		analysis_doc = CVAnalysisResult.create_from_api_response(job_applicant, result)

		# Notify user
		frappe.publish_realtime(
			event="cv_analysis_complete",
			message={
				"applicant": job_applicant,
				"analysis": analysis_doc.name,
				"score": analysis_doc.overall_score,
				"recommendation": analysis_doc.recommendation
			},
			user=doc.owner
		)

		# Send email notification (optional)
		send_analysis_notification(doc, analysis_doc)

		frappe.db.commit()

	except Exception as e:
		frappe.log_error(
			title=f"CV Analysis Failed: {job_applicant}",
			message=str(e)
		)

		# Notify user of failure
		frappe.publish_realtime(
			event="cv_analysis_failed",
			message={
				"applicant": job_applicant,
				"error": str(e)
			},
			user=frappe.session.user
		)


def send_analysis_notification(job_applicant_doc, analysis_doc):
	"""
	Send email notification about CV analysis completion

	Args:
		job_applicant_doc: Job Applicant document
		analysis_doc: CV Analysis Result document
	"""
	try:
		# Get recipients (owner and HR managers)
		recipients = [job_applicant_doc.owner]

		# Add HR Managers
		hr_managers = frappe.get_all(
			"Has Role",
			filters={"role": "HR Manager", "parenttype": "User"},
			fields=["parent"]
		)
		recipients.extend([r.parent for r in hr_managers])

		# Remove duplicates
		recipients = list(set(recipients))

		# Prepare email content
		subject = f"CV Analysis Complete: {job_applicant_doc.applicant_name}"

		message = f"""
		<h3>CV Analysis Results</h3>
		<p><strong>Applicant:</strong> {job_applicant_doc.applicant_name}</p>
		<p><strong>Position:</strong> {job_applicant_doc.job_title or 'N/A'}</p>
		<p><strong>Overall Score:</strong> {analysis_doc.overall_score}/100</p>
		<p><strong>Recommendation:</strong> {analysis_doc.recommendation}</p>

		<p><a href="{frappe.utils.get_url()}/app/cv-analysis-result/{analysis_doc.name}">
			View Full Analysis
		</a></p>
		"""

		# Send email
		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=message,
			reference_doctype="CV Analysis Result",
			reference_name=analysis_doc.name
		)

	except Exception as e:
		frappe.log_error(
			title="CV Analysis Notification Failed",
			message=str(e)
		)


@frappe.whitelist()
def trigger_manual_analysis(job_applicant):
	"""
	Manually trigger CV analysis for a job applicant

	Args:
		job_applicant: Job Applicant docname

	Returns:
		dict: Status message
	"""
	doc = frappe.get_doc("Job Applicant", job_applicant)

	if not doc.resume_attachment:
		frappe.throw(_("No resume attachment found"))

	# Trigger analysis
	frappe.enqueue(
		analyze_cv_async,
		queue="long",
		timeout=300,
		job_applicant=doc.name,
		cv_file_url=doc.resume_attachment
	)

	return {
		"message": _("CV analysis has been queued"),
		"status": "queued"
	}


@frappe.whitelist()
def get_latest_analysis(job_applicant):
	"""
	Get the latest CV analysis for a job applicant

	Args:
		job_applicant: Job Applicant docname

	Returns:
		dict: Analysis data or None
	"""
	analyses = frappe.get_all(
		"CV Analysis Result",
		filters={"job_applicant": job_applicant},
		fields=["name", "overall_score", "recommendation", "analysis_date"],
		order_by="analysis_date desc",
		limit=1
	)

	if analyses:
		return frappe.get_doc("CV Analysis Result", analyses[0].name).as_dict()

	return None
