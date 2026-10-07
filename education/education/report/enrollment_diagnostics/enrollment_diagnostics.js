// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports['Enrollment Diagnostics'] = {
  filters: [
    {
      fieldname: 'academic_year',
      label: __('Academic Year'),
      fieldtype: 'Link',
      options: 'Academic Year',
      description: __('The year being enrolled into. Defaults to the newest year.'),
    },
    {
      fieldname: 'previous_academic_year',
      label: __('Compare With'),
      fieldtype: 'Link',
      options: 'Academic Year',
      description: __('Defaults to the year before.'),
    },
    {
      fieldname: 'branch',
      label: __('Branch'),
      fieldtype: 'Select',
      options: '\nMain\nMBS #2\nMBS Dembi Dollo',
    },
    {
      fieldname: 'program',
      label: __('Program'),
      fieldtype: 'Link',
      options: 'Program',
    },
    {
      fieldname: 'severity',
      label: __('Severity'),
      fieldtype: 'Select',
      options: '\nBlocked\nReview\nInfo',
    },
    {
      fieldname: 'category',
      label: __('Category'),
      fieldtype: 'Select',
      options: '\nIdentity\nPromotion\nEnrollment\nSection\nExit\nStatus\nAccount\nExam\nData Quality',
    },
    {
      fieldname: 'student',
      label: __('Student'),
      fieldtype: 'Link',
      options: 'Student',
    },
  ],

  onload(report) {
    if (!report.get_filter_value('academic_year')) {
      frappe.db
        .get_list('Academic Year', { fields: ['name'], order_by: 'year_start_date desc', limit: 1 })
        .then((rows) => rows.length && report.set_filter_value('academic_year', rows[0].name))
    }
    report.page.add_inner_button(__('Program Enrollment Tool'), () =>
      frappe.set_route('Form', 'Program Enrollment Tool')
    )
  },

  formatter(value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data)
    if (column.fieldname === 'severity' && data) {
      const color = { Blocked: 'red', Review: 'orange', Info: 'blue' }[data.severity]
      if (color) value = `<span class="indicator-pill ${color}">${value}</span>`
    }
    return value
  },
}
