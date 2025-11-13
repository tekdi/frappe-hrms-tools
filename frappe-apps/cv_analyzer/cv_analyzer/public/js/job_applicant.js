/**
 * Job Applicant Form Enhancement for CV Analysis
 */

frappe.ui.form.on('Job Applicant', {
	refresh: function(frm) {
		// Add custom button for manual CV analysis
		if (frm.doc.resume_attachment && !frm.is_new()) {
			frm.add_custom_button(__('Analyze CV'), function() {
				analyze_cv(frm);
			}, __('Actions'));
		}

		// Add button to view latest analysis
		if (!frm.is_new()) {
			frm.add_custom_button(__('View CV Analysis'), function() {
				view_latest_analysis(frm);
			}, __('View'));
		}

		// Load and display latest analysis summary
		if (!frm.is_new()) {
			load_analysis_summary(frm);
		}

		// Listen for real-time updates
		setup_realtime_updates(frm);
	}
});

function analyze_cv(frm) {
	frappe.call({
		method: 'cv_analyzer.api.job_applicant.trigger_manual_analysis',
		args: {
			job_applicant: frm.doc.name
		},
		freeze: true,
		freeze_message: __('Queuing CV analysis...'),
		callback: function(r) {
			if (r.message) {
				frappe.show_alert({
					message: r.message.message,
					indicator: 'blue'
				}, 5);
			}
		}
	});
}

function view_latest_analysis(frm) {
	frappe.call({
		method: 'cv_analyzer.api.job_applicant.get_latest_analysis',
		args: {
			job_applicant: frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				// Navigate to the analysis
				frappe.set_route('Form', 'CV Analysis Result', r.message.name);
			} else {
				frappe.msgprint(__('No CV analysis found for this applicant'));
			}
		}
	});
}

function load_analysis_summary(frm) {
	frappe.call({
		method: 'cv_analyzer.api.job_applicant.get_latest_analysis',
		args: {
			job_applicant: frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				display_analysis_summary(frm, r.message);
			}
		}
	});
}

function display_analysis_summary(frm, analysis) {
	// Remove existing summary
	frm.dashboard.clear_headline();

	// Create summary HTML
	let indicator_color = get_recommendation_color(analysis.recommendation);

	let summary_html = `
		<div class="row">
			<div class="col-md-12">
				<div class="cv-analysis-summary" style="padding: 15px; background: #f9f9f9; border-radius: 5px; margin-bottom: 15px;">
					<h4 style="margin-top: 0;">
						<span class="indicator ${indicator_color}">CV Analysis</span>
					</h4>
					<div class="row">
						<div class="col-sm-3">
							<div class="stat-box">
								<h5>Overall Score</h5>
								<h2>${analysis.overall_score}/100</h2>
							</div>
						</div>
						<div class="col-sm-3">
							<div class="stat-box">
								<h5>Recommendation</h5>
								<h4 style="text-transform: capitalize;">${analysis.recommendation.replace('_', ' ')}</h4>
							</div>
						</div>
						<div class="col-sm-6">
							<div class="stat-box">
								<h5>Analysis Date</h5>
								<p>${frappe.datetime.str_to_user(analysis.analysis_date)}</p>
								<button class="btn btn-sm btn-default" onclick="frappe.set_route('Form', 'CV Analysis Result', '${analysis.name}')">
									View Full Analysis
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	`;

	frm.dashboard.add_section(summary_html);
}

function get_recommendation_color(recommendation) {
	const colors = {
		'strong_yes': 'green',
		'yes': 'green',
		'maybe': 'orange',
		'no': 'red',
		'strong_no': 'red'
	};
	return colors[recommendation] || 'blue';
}

function setup_realtime_updates(frm) {
	// Listen for CV analysis progress
	frappe.realtime.on('cv_analysis_progress', function(data) {
		if (data.applicant === frm.doc.name) {
			if (data.status === 'started') {
				frappe.show_alert({
					message: __('CV analysis in progress...'),
					indicator: 'blue'
				}, 10);
			}
		}
	});

	// Listen for CV analysis completion
	frappe.realtime.on('cv_analysis_complete', function(data) {
		if (data.applicant === frm.doc.name) {
			frappe.show_alert({
				message: __('CV analysis completed! Score: {0}/100', [data.score]),
				indicator: 'green'
			}, 10);

			// Reload to show new analysis
			setTimeout(() => {
				frm.reload_doc();
			}, 2000);
		}
	});

	// Listen for CV analysis failure
	frappe.realtime.on('cv_analysis_failed', function(data) {
		if (data.applicant === frm.doc.name) {
			frappe.show_alert({
				message: __('CV analysis failed: {0}', [data.error]),
				indicator: 'red'
			}, 10);
		}
	});
}
