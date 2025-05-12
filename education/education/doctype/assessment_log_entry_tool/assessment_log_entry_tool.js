// Copyright (c) 2024, Your Organization and contributors
// For license information, please see license.txt

frappe.ui.form.on('Assessment Log Entry Tool', {
  setup: function (frm) {
    frm.add_fetch('assessment_plan', 'student_group', 'student_group');
  },

  refresh: function (frm) {
    // Handle route options if coming from another page (like Assessment Plan)
    if (frappe.route_options) {
      if (frappe.route_options.student_group) {
        frm.set_value('student_group', frappe.route_options.student_group);
      }
      if (frappe.route_options.assessment_plan) {
        frm.set_value('assessment_plan', frappe.route_options.assessment_plan);
      }
      frappe.route_options = null;
    }
    
    frm.disable_save();
    frm.page.clear_indicator();
    frm.page.clear_primary_action();
    
    // Add a "Reset Form" button since this form doesn't use standard Save 
    if (!frm.reset_button_added) {
      $('<button class="btn btn-default btn-sm pull-right" style="margin-top: 10px;">Reset Form</button>')
        .appendTo(frm.fields_dict.result_html.wrapper)
        .on('click', function() {
          frm.set_value('assessment_plan', null);
          frm.set_value('student_group', null);
          frm.set_value('academic_term', null);
          frm.set_value('assessment_criteria', null);
          $(frm.fields_dict.result_html.wrapper).empty();
          frm.doc.students = [];
          frm.refresh_fields();
          frm.reset_button_added = false; // Allow adding button again on refresh
          frm.trigger('refresh');
        });
      frm.reset_button_added = true;
    }
    
    frm.events.maybe_load_table(frm);
  },

  assessment_plan: function(frm) { frm.events.maybe_load_table(frm); },
  student_group: function(frm) { frm.events.maybe_load_table(frm); },
  academic_term: function(frm) { frm.events.maybe_load_table(frm); },
  assessment_criteria: function(frm) { frm.events.maybe_load_table(frm); },

  maybe_load_table: function(frm) {
    $(frm.fields_dict.result_html.wrapper).find('.assessment-table-container').remove();
    frm.page.clear_primary_action();

    if (!frm.doc.assessment_plan || !frm.doc.student_group || !frm.doc.academic_term || !frm.doc.assessment_criteria) {
      return;
    }

    console.log("Loading students for table... All fields are set:", {
      plan: frm.doc.assessment_plan,
      group: frm.doc.student_group,
      term: frm.doc.academic_term,
      criteria: frm.doc.assessment_criteria
    });

    frm.page.set_indicator(__('Loading Students...'), 'blue');
    frappe.call({
      method: 'education.education.api.get_student_group_students',
      args: { student_group: frm.doc.student_group },
      callback: function (r) {
        frm.page.clear_indicator();
        if (r.message && r.message.length > 0) {
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
    // Remove only the table, not the reset button
    $(frm.fields_dict.result_html.wrapper).find('.assessment-table-container').remove();
    
    const students = frm.doc.students || [];
    if (students.length === 0) {
      return;
    }

    let table_html = `
      <div class="assessment-table-container">
        <h4>Assessment Log Entries for ${frm.doc.assessment_criteria}</h4>
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
    table_html += '</tbody></table></div>';
    
    // Append the table before the reset button
    $(frm.fields_dict.result_html.wrapper).prepend(table_html);

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
  }
}); 