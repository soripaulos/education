frappe.ui.form.on('Rank Calculation', {
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

	calculate_ranks: function(frm) {
		if (frm.doc.academic_year && frm.doc.student_group && frm.doc.calculation_type) {
			frm.call({
				doc: frm.doc,
				method: 'calculate_ranks',
				args: {
					doc_name: frm.doc.name
				},
				callback: function(r) {
					if (r.message) {
						frm.set_value('results', r.message.html);
						frappe.msgprint(r.message.message);
					}
				}
			});
		} else {
			frappe.msgprint(__("Please fill in all required fields before calculating ranks."));
		}
	}
}); 