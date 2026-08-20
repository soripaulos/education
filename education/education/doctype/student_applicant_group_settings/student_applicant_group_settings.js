// Copyright (c) 2026, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student Applicant Group Settings", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.dashboard.set_headline(
				frm.doc.allow_new_applicants
					? __("New applications are OPEN for this group in {0}.", [frm.doc.academic_year])
					: __("New applications are CLOSED for this group in {0}.", [frm.doc.academic_year])
			);
		}
	},
});
