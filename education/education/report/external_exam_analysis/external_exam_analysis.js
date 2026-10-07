// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports['External Exam Analysis'] = {
  filters: [
    {
      fieldname: 'exam_type',
      label: __('Exam'),
      fieldtype: 'Select',
      options: '\nGrade 6 Regional Exam\nGrade 8 Regional Exam\nGrade 12 National Exam',
      reqd: 1,
      default: 'Grade 12 National Exam',
    },
    {
      fieldname: 'academic_year',
      label: __('Academic Year'),
      fieldtype: 'Link',
      options: 'Academic Year',
    },
    {
      fieldname: 'program',
      label: __('Program'),
      fieldtype: 'Link',
      options: 'Program',
    },
    {
      fieldname: 'student_group',
      label: __('Section'),
      fieldtype: 'Link',
      options: 'Student Group',
    },
  ],

  formatter(value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data)
    if (column.fieldname === 'result_status' && data) {
      const color = { Pass: 'green', Fail: 'red', Absent: 'orange', Withheld: 'orange' }[data.result_status]
      if (color) value = `<span class="indicator-pill ${color}">${value}</span>`
    }
    return value
  },
}
