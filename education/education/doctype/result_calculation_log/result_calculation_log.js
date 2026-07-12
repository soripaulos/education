// Copyright (c) 2026, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Result Calculation Log', {
	refresh: function (frm) {
		let indicator_map = {
			'Queued': 'orange',
			'In Progress': 'blue',
			'Completed': 'green',
			'Completed with Warnings': 'yellow',
			'Failed': 'red',
		};
		frm.page.set_indicator(__(frm.doc.status), indicator_map[frm.doc.status] || 'gray');

		if (['Queued', 'In Progress'].includes(frm.doc.status)) {
			frm.add_custom_button(__('Refresh Status'), () => frm.reload_doc());
		}
	},
});
