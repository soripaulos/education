// Copyright (c) 2024, Your Organization and contributors
// For license information, please see license.txt

frappe.ui.form.on('Assessment Log Entry Tool', {
  setup: function (frm) {
    frm.add_fetch('assessment_plan', 'student_group', 'student_group');
  },

  refresh: function (frm) {
    frm.disable_save();
    frm.page.clear_indicator();
    frm.page.clear_primary_action();
    frm.events.maybe_load_table(frm);
  },

  assessment_plan: function(frm) { frm.events.maybe_load_table(frm); },
  academic_term: function(frm) { frm.events.maybe_load_table(frm); },
  assessment_criteria: function(frm) { frm.events.maybe_load_table(frm); },

  maybe_load_table: function(frm) {
    $(frm.fields_dict.result_html.wrapper).empty();
    frm.page.clear_primary_action();

    if (!frm.doc.assessment_plan || !frm.doc.student_group || !frm.doc.academic_term || !frm.doc.assessment_criteria) {
      // Optionally, show a message or highlight missing fields
      return;
    }

    frm.page.set_indicator(__('Loading Students...'), 'blue');
    frappe.call({
      method: 'education.education.api.get_student_group_students',
      args: { student_group: frm.doc.student_group },
      callback: function (r) {
        frm.page.clear_indicator();
        if (r.message) {
          frm.doc.students = r.message;
          frm.events.render_table(frm);
        } else {
          frappe.msgprint(__('No students found for the selected group.'));
        }
      },
      error: function (r) {
        frm.page.clear_indicator();
        frappe.show_alert({ message: __('Error fetching student data.'), indicator: 'red' });
      },
    });
  },

  render_table: function (frm) {
    $(frm.fields_dict.result_html.wrapper).empty();
    const students = frm.doc.students || [];
    let table_html = `
      <table class="table table-bordered assessment-log-entry-tool">
        <thead>
          <tr>
            <th>Student</th>
            <th>Student Name</th>
            <th>Score</th>
            <th>Comments</th>
          </tr>
        </thead>
        <tbody>
    `;
    students.forEach((s) => {
      table_html += `
        <tr data-student="${s.student}">
          <td>${s.student}</td>
          <td>${s.student_name || ''}</td>
          <td><input type="number" class="student-score" data-student="${s.student}" style="width: 80px;" /></td>
          <td><input type="text" class="student-comment" data-student="${s.student}" style="width: 100%;" /></td>
        </tr>
      `;
    });
    table_html += '</tbody></table>';
    $(frm.fields_dict.result_html.wrapper).html(table_html);

    // Handle score/comment changes
    $(frm.fields_dict.result_html.wrapper).find('input.student-score, input.student-comment').on('change', function (e) {
      const $input = $(e.target);
      const student = $input.data('student');
      const $row = $(this).closest('tr');
      const score = parseFloat($row.find('input.student-score').val()) || 0;
      const comments = $row.find('input.student-comment').val() || '';
      frappe.call({
        method: 'education.education.api.log_assessment_entry',
        args: {
          student: student,
          assessment_plan: frm.doc.assessment_plan,
          assessment_criteria: frm.doc.assessment_criteria,
          score: score,
          comments: comments,
        },
        callback: function (r) {
          if (r.message && r.message.status === 'success') {
            frappe.show_alert({ message: __('Entry logged for {0}', [student]), indicator: 'green' });
          } else {
            frappe.show_alert({ message: __('Failed to log entry for {0}', [student]), indicator: 'red' });
          }
        },
        error: function () {
          frappe.show_alert({ message: __('Error logging entry for {0}', [student]), indicator: 'red' });
        },
      });
    });
  },

  // On save, clear all fields to reset the form for the next entry
  after_save: function(frm) {
    // Clear all fields except route_options
    frm.set_value('assessment_plan', null);
    frm.set_value('student_group', null);
    frm.set_value('academic_term', null);
    frm.set_value('assessment_criteria', null);
    $(frm.fields_dict.result_html.wrapper).empty();
    frm.doc.students = [];
    frm.refresh_fields();
  }
}); 