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
	
	if (!frm.doc.academic_year) {
		frappe.msgprint(__('Please select an Academic Year'));
		return;
	}
	
	if (frm.doc.calculation_type === 'Term Results' && !frm.doc.semester) {
		frappe.msgprint(__('Please select a Semester for Term Results calculation'));
		return;
	}

	// Show confirmation dialog
	let message = `Calculate ${frm.doc.calculation_type} for ${frm.doc.academic_year}`;
	if (frm.doc.semester) {
		message += ` - ${frm.doc.semester}`;
	}
	if (frm.doc.student_group) {
		message += ` (${frm.doc.student_group})`;
	} else {
		message += ` (All Student Groups)`;
	}
	message += '?';

	frappe.confirm(
		message,
		function() {
			// User confirmed, proceed with calculation
			frappe.show_alert({
				message: __('Starting calculation...'),
				indicator: 'blue'
			});

			frappe.call({
				method: 'education.education.education.doctype.result_calculation_tool.result_calculation_tool.calculate_results',
				args: {
					calculation_type: frm.doc.calculation_type,
					academic_year: frm.doc.academic_year,
					semester: frm.doc.semester,
					student_group: frm.doc.student_group
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