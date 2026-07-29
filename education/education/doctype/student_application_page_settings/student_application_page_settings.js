// Copyright (c) 2026, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student Application Page Settings", {
	refresh(frm) {
		const pages = [
			{ key: "mbreg1825", label: "MBReg1825", field: "mbreg1825_html", route: "/mbreg1825" },
			{ key: "apply_dd", label: "Apply DD", field: "apply_dd_html", route: "/apply-dd" },
		];

		pages.forEach((page) => {
			frm.add_custom_button(
				__("Load current page HTML"),
				() => load_from_file(frm, page),
				__(page.label)
			);
			frm.add_custom_button(
				__("Open page"),
				() => window.open(page.route, "_blank"),
				__(page.label)
			);
		});
	},
});

function load_from_file(frm, page) {
	const existing = (frm.doc[page.field] || "").trim();
	const proceed = () =>
		frappe
			.call({
				method:
					"education.education.doctype.student_application_page_settings.student_application_page_settings.load_current_page_html",
				args: { page: page.key },
				freeze: true,
				freeze_message: __("Loading deployed page…"),
			})
			.then((r) => {
				if (r.message) {
					frm.set_value(page.field, r.message);
					frappe.show_alert({
						message: __("Loaded the deployed {0} page. Review, then Save.", [page.label]),
						indicator: "green",
					});
				}
			});

	if (existing) {
		frappe.confirm(
			__("This replaces your current {0} HTML with the deployed version. Continue?", [
				page.label,
			]),
			proceed
		);
	} else {
		proceed();
	}
}
