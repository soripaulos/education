frappe.ui.form.on('Bulk Score Entry', {
	onload: function(frm) {
		frm.set_query('academic_term', function() {
			return {
				filters: {
					'academic_year': frm.doc.academic_year
				}
			};
		});
	},

	academic_year: function(frm) {
		frm.set_value('academic_term', '');
	},

	assessment_criteria: function(frm) {
		frm.max_score_for_criteria = null; // Reset cache
		if (frm.doc.students && frm.doc.students.length > 0) {
			frm.clear_table('students');
			frm.refresh_field('students');
			frappe.msgprint(__("Student list cleared because Assessment Criteria was changed. Please fetch students again."));
		}
	},

	get_students: function(frm) {
		if (frm.doc.student_group && frm.doc.assessment_criteria) {
			frappe.call({
				method: "education.education.doctype.bulk_score_entry.bulk_score_entry.get_students",
				args: {
					student_group: frm.doc.student_group
				},
				callback: function(r) {
					if (r.message) {
						frm.clear_table('students');
						r.message.forEach(function(d) {
							var child = frm.add_child('students');
							child.student = d[0];
							child.student_name = d[1];
						});
						frm.refresh_field('students');
					}
				}
			});
		} else {
			frappe.msgprint(__("Please select a Student Group and Assessment Criteria first."));
		}
	}
});

frappe.ui.form.on('Bulk Score Entry Student', {
	score: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];

		function validate_row_score(max_score) {
			if (row.score > max_score) {
				frappe.msgprint(__("Score for {0} cannot be greater than {1}", [row.student_name, max_score]));
				frappe.model.set_value(cdt, cdn, 'score', max_score);
			}
			if (row.score < 0) {
				frappe.msgprint(__("Score cannot be negative."));
				frappe.model.set_value(cdt, cdn, 'score', 0);
			}
		}

		if (frm.doc.assessment_criteria) {
			if (frm.max_score_for_criteria) {
				validate_row_score(frm.max_score_for_criteria);
			} else {
				frappe.call({
					method: 'education.education.doctype.bulk_score_entry.bulk_score_entry.get_max_score',
					args: {
						assessment_criteria: frm.doc.assessment_criteria
					},
					callback: function(r) {
						if (r.message) {
							frm.max_score_for_criteria = r.message;
							validate_row_score(r.message);
						} else {
							frappe.msgprint(__("Max score not defined for {0}", [frm.doc.assessment_criteria]));
							frappe.model.set_value(cdt, cdn, 'score', null);
						}
					}
				});
			}
		}
	}
}); 