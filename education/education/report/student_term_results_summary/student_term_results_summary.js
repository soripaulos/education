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
    {
      fieldname: 'exam',
      label: __('Exam(s)'),
      fieldtype: 'MultiSelectList',
      get_data: function(txt) {
        return frappe.db.get_link_options('Assessment Criteria', txt);
      },
      on_change: function() {
        // Refresh report when exam selection changes
        frappe.query_report.refresh();
      }
    },
  ],
  onload: function(report) {
    // Show helpful message about exam selection
    frappe.msgprint({
      title: __('Exam Selection'),
      message: __('<b>Tip:</b> Select specific exam(s) to report on.<br><br>• <b>1 exam selected:</b> Shows individual exam scores<br>• <b>Multiple exams:</b> Shows summed scores<br>• <b>No selection:</b> Shows all exams summed'),
      indicator: 'blue'
    });
  }
}
