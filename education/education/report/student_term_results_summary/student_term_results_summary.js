// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports['Student Term Results Summary'] = {
  filters: [
    {
      fieldname: 'student_group',
      label: __('Student Group'),
      fieldtype: 'Link',
      options: 'Student Group',
      reqd: 1,
    },
    {
      fieldname: 'academic_year',
      label: __('Academic Year'),
      fieldtype: 'Link',
      options: 'Academic Year',
      reqd: 1,
    },
    {
      fieldname: 'semester',
      label: __('Semester'),
      fieldtype: 'Link',
      options: 'Academic Term',
    },
  ],
}
