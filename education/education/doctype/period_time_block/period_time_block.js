// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Period Time Block', {
  refresh(frm) {
    frm.set_query('program', function () {
      return {
        filters: {
          name: ['!=', ''],
        },
      }
    })
  },
})
