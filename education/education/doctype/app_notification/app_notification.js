// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

const APP_NOTIFICATION_MODULE = "education.education.doctype.app_notification.app_notification";

frappe.ui.form.on("App Notification", {
	refresh(frm) {
		if (frm.doc.docstatus === 0 && !frm.is_new()) {
			show_recipient_preview(frm);
		}

		if (frm.doc.docstatus !== 1) return;

		frm.add_custom_button(__("Delivery Report"), () => {
			frappe.set_route("List", "App Notification Delivery", { notification: frm.doc.name });
		});

		frm.add_custom_button(__("Refresh Delivery Status"), () => {
			frappe.call({
				method: `${APP_NOTIFICATION_MODULE}.refresh_delivery_status`,
				args: { notification_name: frm.doc.name },
				freeze: true,
				callback: () => frm.reload_doc(),
			});
		});

		if (frm.doc.failed_count) {
			frm.add_custom_button(__("Resend to Failed Devices"), () => {
				frappe.call({
					method: `${APP_NOTIFICATION_MODULE}.resend_failed`,
					args: { notification_name: frm.doc.name },
					freeze: true,
					callback: () => frm.reload_doc(),
				});
			});
		}

		if (frm.doc.status === "Draft" || (frm.doc.status === "Failed" && !frm.doc.sent_count)) {
			frm.add_custom_button(__("Send Again"), () => {
				frappe.call({
					method: `${APP_NOTIFICATION_MODULE}.send_test_notification`,
					args: { notification_name: frm.doc.name },
					freeze: true,
					callback: () => frm.reload_doc(),
				});
			});
		}
	},

	before_submit(frm) {
		return new Promise((resolve, reject) => {
			frappe.call({
				method: `${APP_NOTIFICATION_MODULE}.get_recipient_preview`,
				args: recipient_args(frm),
				callback: (r) => {
					const p = r.message || {};
					frappe.confirm(
						__("This will notify {0} student(s) ({1} with the app on a phone). Send now?", [
							p.students || 0,
							p.with_device || 0,
						]),
						resolve,
						() => reject(),
					);
				},
				error: () => reject(),
			});
		});
	},

	send_to_all_students: show_recipient_preview,
});

frappe.ui.form.on("App Notification Student", {
	student: (frm) => show_recipient_preview(frm),
	students_remove: (frm) => show_recipient_preview(frm),
});

frappe.ui.form.on("App Notification Student Group", {
	student_group: (frm) => show_recipient_preview(frm),
	student_groups_remove: (frm) => show_recipient_preview(frm),
});

function recipient_args(frm) {
	return {
		send_to_all_students: frm.doc.send_to_all_students || 0,
		student_groups: (frm.doc.student_groups || []).map((r) => r.student_group).filter(Boolean),
		students: (frm.doc.students || []).map((r) => r.student).filter(Boolean),
	};
}

function show_recipient_preview(frm) {
	if (frm.doc.docstatus !== 0) return;
	frappe.call({
		method: `${APP_NOTIFICATION_MODULE}.get_recipient_preview`,
		args: recipient_args(frm),
		callback: (r) => {
			const p = r.message || {};
			frm.dashboard.clear_headline();
			frm.dashboard.set_headline(
				__("Will notify {0} student(s), {1} with the app on a phone.", [p.students || 0, p.with_device || 0]),
				p.students ? "blue" : "orange",
			);
		},
	});
}
