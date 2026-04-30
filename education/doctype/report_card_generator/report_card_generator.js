// Copyright (c) 2026, Makkobilli School
// For license information, please see license.txt

frappe.ui.form.on('Report Card Generator', {
	refresh: function(frm) {
		frm.page.set_primary_action(__('Generate Report Cards'), function() {
			generate_report_cards(frm);
		});
	},

	generate_btn: function(frm) {
		generate_report_cards(frm);
	}
});

function generate_report_cards(frm) {
	// Validate required fields
	if (!frm.doc.academic_year) {
		frappe.msgprint(__('Please select an Academic Year'));
		return;
	}

	if (frm.doc.generation_mode === 'Single Student' && !frm.doc.student) {
		frappe.msgprint(__('Please select a Student'));
		return;
	}

	if (frm.doc.generation_mode === 'Student Group' && !frm.doc.student_group) {
		frappe.msgprint(__('Please select a Student Group'));
		return;
	}

	// Show confirmation dialog
	let action_text = frm.doc.result_action === 'Save as Draft' ? 'save as drafts' : 'save and submit';
	let message = `Generate Report Cards for ${frm.doc.academic_year}`;
	if (frm.doc.generation_mode === 'Single Student' && frm.doc.student) {
		message += ` — Student: ${frm.doc.student}`;
	} else if (frm.doc.generation_mode === 'Student Group' && frm.doc.student_group) {
		message += ` — Group: ${frm.doc.student_group}`;
	} else {
		message += ' — All Students';
	}
	message += ` and ${action_text}?`;

	frappe.confirm(
		message,
		function() {
			frappe.show_alert({
				message: __('Generating report cards...'),
				indicator: 'blue'
			});

			let method = '';
			let args = { academic_year: frm.doc.academic_year };

			if (frm.doc.generation_mode === 'Single Student') {
				method = 'education.education.api.generate_student_report_cards';
				args.student = frm.doc.student;
			} else if (frm.doc.generation_mode === 'Student Group') {
				method = 'education.education.api.generate_student_report_cards';
				args.student_group = frm.doc.student_group;
			} else {
				method = 'education.education.api.generate_student_report_cards';
			}

			frappe.call({
				method: method,
				args: args,
				freeze: true,
				freeze_message: __('Generating report cards...'),
				callback: function(r) {
					if (r.message) {
						let result = r.message;
						let msg = '';

						if (Array.isArray(result)) {
							// Batch results (group or all)
							let created = result.filter(x => x.action !== 'Error').length;
							let errors = result.filter(x => x.action === 'Error').length;
							msg = `<b>Generated:</b> ${created} | <b>Errors:</b> ${errors}`;
							if (errors > 0) {
								msg += '<br><details><summary>Show Errors</summary>';
								for (let i of result) {
									if (i.action === 'Error') {
										msg += `<br>${i.student || i.error}: ${i.error}`;
									}
								}
								msg += '</details>';
							}
							frappe.msgprint({ title: __('Done'), message: msg });
						} else {
							// Single result
							if (result.action === 'Created' || result.action === 'Updated') {
								msg = `Report card ${result.action.toLowerCase()}: ${result.name}`;
								frappe.msgprint({ title: __('Done'), message: msg });
							} else {
								msg = result.error || JSON.stringify(result);
								frappe.msgprint({ title: __('Error'), message: msg, indicator: 'red' });
							}
						}

						frm.set_value('generation_result', msg);
						frappe.show_alert({
							message: result.action || 'Done',
							indicator: result.action === 'Error' ? 'red' : 'green'
						});
					}
				},
				error: function(r) {
					frappe.msgprint({
						title: __('Error'),
						message: __('Generation failed: ') + (r.message || 'Unknown error'),
						indicator: 'red'
					});
				}
			});
		}
	);
}
