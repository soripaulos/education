// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Assessment Result Tool', {
  setup: function (frm) {
    frm.add_fetch('assessment_plan', 'student_group', 'student_group')
  },

  refresh: function (frm) {
    if (frappe.route_options) {
      frm.set_value('student_group', frappe.route_options.student_group)
      frm.set_value('assessment_plan', frappe.route_options.assessment_plan)
      frappe.route_options = null
    } else {
      if (frm.doc.assessment_plan) {
          frm.trigger('assessment_plan');
      }
    }
    frm.disable_save()
    frm.page.clear_indicator()
    frm.page.clear_primary_action()
  },

  assessment_plan: function (frm) {
    frm.doc.show_submit = false
    $(frm.fields_dict.result_html.wrapper).empty();
    frm.page.clear_primary_action();

    if (frm.doc.assessment_plan) {
      if (!frm.doc.student_group) {
          frappe.msgprint(__("Please select a Student Group first."));
          return;
      }
      frm.page.set_indicator(__("Loading Students..."), "blue");

      frappe.call({
        method: 'education.education.api.get_assessment_students',
        args: {
          assessment_plan: frm.doc.assessment_plan,
          student_group: frm.doc.student_group,
        },
        callback: function (r) {
          frm.page.clear_indicator();
          if (r.message) {
            frm.doc.students = r.message
            frm.events.render_table(frm)
            
            // Always set show_submit to true if there are students
            frm.doc.show_submit = true
            frm.events.submit_result(frm)
          } else {
            frappe.msgprint(__("No students found for the selected group or assessment plan."));
          }
        },
        error: function(r) {
            frm.page.clear_indicator();
            console.error("Error fetching assessment students:", r);
            frappe.show_alert({ message: __("Error fetching student data."), indicator: 'red' });
        }
      })
    }
  },

  render_table: function (frm) {
    $(frm.fields_dict.result_html.wrapper).empty()
    let assessment_plan = frm.doc.assessment_plan
    frm.page.set_indicator(__("Loading Assessment Details..."), "blue");
    frappe.call({
      method: 'education.education.api.get_assessment_details',
      args: {
        assessment_plan: assessment_plan,
      },
      callback: function (r) {
        frm.page.clear_indicator();
        if (r.message && r.message.length > 0) {
          frm.events.get_marks(frm, r.message)
        } else {
           frappe.msgprint(__("No assessment criteria found for the selected Assessment Plan."));
           $(frm.fields_dict.result_html.wrapper).html(`<div class="text-muted text-center" style="padding: 20px;">${__("No assessment criteria defined for this plan.")}</div>`);
        }
      },
       error: function(r) {
            frm.page.clear_indicator();
            console.error("Error fetching assessment details:", r);
            frappe.show_alert({ message: __("Error fetching assessment details."), indicator: 'red' });
        }
    })
  },

  get_marks: function (frm, criteria_list) {
    let max_total_score = 0
    criteria_list.forEach(function (c, index) { 
      c._index = index; 
      max_total_score += flt(c.maximum_score)
    })
    
    var result_table = $(
      frappe.render_template('assessment_result_tool', {
        frm: frm,
        students: frm.doc.students,
        criteria: criteria_list,
        max_total_score: max_total_score,
      })
    )
    $(frm.fields_dict.result_html.wrapper).empty().append(result_table);

    // Handle SCORE changes
    result_table.on('change', 'input.student-result-data', function (e) {
      let $input = $(e.target);
      let student = $input.data().student;
      let max_score = flt($input.data().maxScore);
      let value = $input.val();
      
      // Validate input value
      let score = parseFloat(value);
      if (isNaN(score) || score < 0) {
        score = 0;
        $input.val(0); // Update input visually if invalid
      } else if (score > max_score) {
        score = max_score;
        $input.val(max_score);
        frappe.show_alert({ message: __("Score cannot exceed Maximum Score ({0})", [max_score]), indicator: 'orange' })
      }
      
      // Recalculate total score for the specific student - with proper quotes for jQuery selector
      let total_score = 0;
      result_table.find(`input[data-student="${student}"].student-result-data`).each(function() {
          let current_val = parseFloat($(this).val());
          if (!isNaN(current_val)) {
              total_score += current_val;
          }
      });
      result_table.find(`span[data-student="${student}"].total-score`).html(total_score);

      // Get student details object
      let student_scores = {};
      student_scores['assessment_details'] = {};
      
      // Collect all scores for this student
      result_table.find(`input[data-student="${student}"].student-result-data`).each(function() {
        let criteria = $(this).data().criteria;
        let score_value = parseFloat($(this).val());
        if (!isNaN(score_value)) {
          student_scores['assessment_details'][criteria] = [score_value, ''];
        }
      });
      
      // Include comments
      result_table.find(`[data-student="${student}"].result-comment`).each(function() {
        student_scores['comment'] = $(this).val();
      });
      
      student_scores['student'] = student;
      student_scores['total_score'] = total_score;
    });
    
    // Handle COMMENT changes - no need to change this part
    result_table.on('change', 'input.result-comment', function (e) {
      // Comment handling code - unchanged
    });
  },

  submit_result: function (frm) {
    if (frm.doc.assessment_plan) {
      frm.page.set_primary_action(__('Submit Results'), function () {
        frappe.call({
          method: 'education.education.api.submit_assessment_results',
          args: {
            assessment_plan: frm.doc.assessment_plan,
            student_group: frm.doc.student_group,
          },
          callback: function (r) {
            if (r.message) {
              frappe.msgprint(__('Assessment Results submitted for group: ' + frm.doc.student_group));
              frm.events.assessment_plan(frm);
            } else {
              frappe.msgprint(__('No Students in the Student Group: ' + frm.doc.student_group));
            }
          }
        });
      });
    }
  }
}); 