// Copyright (c) 2026, Frappe Technologies and contributors
// For license information, please see license.txt

const PAGES = [
	{ key: "mbreg1825", label: "MBReg1825", field: "mbreg1825_html", hash: "mbreg1825_source_hash", route: "/mbreg1825" },
	{ key: "apply_dd", label: "Apply DD", field: "apply_dd_html", hash: "apply_dd_source_hash", route: "/apply-dd" },
];

frappe.ui.form.on("Student Application Page Settings", {
	refresh(frm) {
		PAGES.forEach((page) => {
			frm.add_custom_button(__("Load current page HTML"), () => load_from_file(frm, page), __(page.label));
			frm.add_custom_button(__("Open page"), () => window.open(page.route, "_blank"), __(page.label));
		});
		render_status(frm);
	},
});

// Which page is actually being served, and whether an override has fallen
// behind the deployed file. Without this the form gives no clue that a stale
// override is shadowing every deploy.
function render_status(frm) {
	const wrapper = frm.get_field("override_status_html");
	if (!wrapper) return;

	frappe
		.call({
			method:
				"education.education.doctype.student_application_page_settings.student_application_page_settings.get_page_status",
		})
		.then((r) => {
			const status = r.message || {};
			const rows = PAGES.map((page) => {
				const s = status[page.key] || {};
				let tone = "#166534";
				let background = "#dcfce7";
				let serving = "Serving the deployed page";

				if (s.override_enabled && s.stale) {
					tone = "#991b1b";
					background = "#fee2e2";
					serving =
						"Serving the Desk override &mdash; <b>the deployed page has changed since it was loaded</b>";
				} else if (s.override_enabled) {
					tone = "#92400e";
					background = "#fef3c7";
					serving = "Serving the Desk override &mdash; deploys do not reach this page";
				}

				const extras = [
					s.has_css ? "CSS" : null,
					s.has_js ? "JS" : null,
					s.context_script ? `context script: ${frappe.utils.escape_html(s.context_script)}` : null,
				].filter(Boolean);

				return `
					<div style="background:${background};color:${tone};border-radius:6px;padding:10px 12px;margin-bottom:8px">
						<b>${frappe.utils.escape_html(s.route || page.route)}</b> &mdash; ${serving}
						${extras.length ? `<div style="margin-top:4px;opacity:.85">Injected: ${extras.join(", ")}</div>` : ""}
					</div>`;
			}).join("");

			wrapper.$wrapper.html(rows);
		});
}

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
				if (!r.message) return;
				frm.set_value(page.field, r.message.html);
				// Recorded alongside the HTML so a later deploy can be detected
				// as having moved past this copy.
				frm.set_value(page.hash, r.message.source_hash || "");
				frappe.show_alert({
					message: __("Loaded the deployed {0} page. Review, then Save.", [page.label]),
					indicator: "green",
				});
			});

	if (existing) {
		frappe.confirm(
			__("This replaces your current {0} HTML with the deployed version. Continue?", [page.label]),
			proceed
		);
	} else {
		proceed();
	}
}
