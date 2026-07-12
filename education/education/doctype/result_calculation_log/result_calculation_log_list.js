frappe.listview_settings['Result Calculation Log'] = {
	add_fields: ['status'],
	get_indicator: function (doc) {
		let colors = {
			'Queued': 'orange',
			'In Progress': 'blue',
			'Completed': 'green',
			'Completed with Warnings': 'yellow',
			'Failed': 'red',
		};
		return [__(doc.status), colors[doc.status] || 'gray', 'status,=,' + doc.status];
	},
};
