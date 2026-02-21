frappe.ui.form.on('Student Assessment Score', {
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
		if (frm.doc.assessment_criteria) {
			frappe.call({
				method: 'education.education.doctype.bulk_score_entry.bulk_score_entry.get_max_score',
				args: {
					assessment_criteria: frm.doc.assessment_criteria
				},
				callback: function(r) {
					if (r.message) {
						frm.set_value('max_score', r.message);
						frm.refresh_field('max_score');
					}
				}
			});
		}
	}
}); 