// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports['Enrollment Statistics'] = {
  filters: [
    {
      fieldname: 'academic_year',
      label: __('Academic Year'),
      fieldtype: 'Link',
      options: 'Academic Year',
      description: __('Defaults to the newest year.'),
    },
    {
      fieldname: 'previous_academic_year',
      label: __('Compare With'),
      fieldtype: 'Link',
      options: 'Academic Year',
    },
    {
      fieldname: 'branch',
      label: __('Branch'),
      fieldtype: 'Select',
      options: '\nMain\nMBS #2\nMBS Dembi Dollo',
    },
  ],

  onload(report) {
    if (!report.get_filter_value('academic_year')) {
      frappe.db
        .get_list('Academic Year', { fields: ['name'], order_by: 'year_start_date desc', limit: 1 })
        .then((rows) => rows.length && report.set_filter_value('academic_year', rows[0].name))
    }
  },
}
