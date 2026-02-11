// Copyright (c) 2024, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Result Calculation Tool', {
	refresh: function(frm) {
		// Set up the calculate button
		frm.page.set_primary_action(__('Calculate Results'), function() {
			calculate_results(frm);
		});
	},

	calculate_button: function(frm) {
		calculate_results(frm);
	}
});

function calculate_results(frm) {
	// Validate required fields
	if (!frm.doc.calculation_type) {
		frappe.msgprint(__('Please select a Calculation Type'));
		return;
	}

	// Show confirmation dialog
	let action_text = frm.doc.result_action === 'Save as Draft' ? 'save as drafts' : 'calculate and submit';
	let message = `Calculate ${frm.doc.calculation_type}`;
	
	// Add academic year to message if specified
	if (frm.doc.academic_year) {
		message += ` for ${frm.doc.academic_year}`;
	} else {
		message += ` for all academic years`;
	}
	
	// Add semester to message if specified
	if (frm.doc.semester) {
		message += ` - ${frm.doc.semester}`;
	} else if (frm.doc.calculation_type === 'Term Results') {
		message += ` - all semesters`;
	}
	
	// Add student group to message
	if (frm.doc.student_group) {
		message += ` (${frm.doc.student_group})`;
	} else {
		message += ` (All Student Groups)`;
	}
	message += ` and ${action_text}?`;

	frappe.confirm(
		message,
		function() {
			// User confirmed, proceed with calculation
			frappe.show_alert({
				message: __('Starting calculation...'),
				indicator: 'blue'
			});

			frappe.call({
				method: 'education.education.api.calculate_results',
				args: {
					calculation_type: frm.doc.calculation_type,
					academic_year: frm.doc.academic_year,
					semester: frm.doc.semester,
					student_group: frm.doc.student_group,
					result_action: frm.doc.result_action
				},
				callback: function(r) {
					if (r.message && r.message.status === 'success') {
						frappe.show_alert({
							message: r.message.message,
							indicator: 'green'
						});
					} else if (r.message && r.message.status === 'error') {
						frappe.show_alert({
							message: r.message.message,
							indicator: 'red'
						});
					}
				},
				error: function(r) {
					frappe.show_alert({
						message: __('Calculation failed. Please check the error log.'),
						indicator: 'red'
					});
				}
			});
		}
	);
} 