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
    frm.page.clear_primary_action(); 
  },

  assessment_plan: function (frm) {
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

    result_table.on('change', 'input.student-result-data', function (e) {
      let $input = $(e.target)
      let student = $input.data().student
      let assessment_criteria = $input.data().criteria
      let max_score = flt($input.data().maxScore)
      let score = parseFloat($input.val())

      if (isNaN(score) || score < 0) {
        score = 0;
        $input.val(0);
      } else if (score > max_score) {
        score = max_score;
        $input.val(max_score);
        frappe.show_alert({ message: __("Score cannot exceed Maximum Score ({0})", [max_score]), indicator: 'orange' })
      } else {
         $input.val(score); 
      }
      
      let current_total_score = 0;
      result_table.find(`input[data-student=${student}].student-result-data`).each(function() {
          let current_val = parseFloat($(this).val());
          if (!isNaN(current_val)) {
              current_total_score += current_val;
          }
      });
      result_table.find(`span[data-student=${student}].total-score`).html(current_total_score);

      console.log(`Logging score for ${student} - ${assessment_criteria}: ${score}`);
      frappe.call({
        method: 'education.education.api.log_assessment_entry', 
        args: {
          student: student,
          assessment_plan: frm.doc.assessment_plan,
          assessment_criteria: assessment_criteria,
          score: score,
        },
        callback: function (r) {
          if (r.message && r.message.status === 'success') {
             console.log(`Score logged successfully: ${r.message.log_entry_name}`);
             $input.addClass('highlight-success');
             setTimeout(() => { $input.removeClass('highlight-success'); }, 1000);
          } else {
             console.error("Failed to log score:", r);
             frappe.show_alert({ message: __("Failed to log score for {0}", [assessment_criteria]), indicator: 'red' });
             $input.addClass('highlight-error');
             setTimeout(() => { $input.removeClass('highlight-error'); }, 1500);
          }
        },
        error: function(r) {
            console.error("API Error logging score:", r);
            frappe.show_alert({ message: __("API Error logging score for {0}", [assessment_criteria]), indicator: 'red' });
             $input.addClass('highlight-error');
             setTimeout(() => { $input.removeClass('highlight-error'); }, 1500);
        }
      });
    });

    result_table.on('change', 'input.result-comment', function (e) {
        let $input = $(e.target);
        let student = $input.data().student;
        let comments = $input.val();

        let first_criteria_input = result_table.find(`input[data-student=${student}].student-result-data`).first();
        if (!first_criteria_input.length) {
            console.error("Could not find criteria input to associate comment with for student:", student);
            return;
        }
        let assessment_criteria_for_comment = first_criteria_input.data().criteria;
        let score_for_comment = parseFloat(first_criteria_input.val()) || 0;

        console.log(`Logging comment for ${student} (associated with ${assessment_criteria_for_comment}): ${comments}`);
        frappe.call({
            method: 'education.education.api.log_assessment_entry', 
            args: {
              student: student,
              assessment_plan: frm.doc.assessment_plan,
              assessment_criteria: assessment_criteria_for_comment, 
              score: score_for_comment,
              comments: comments
            },
            callback: function (r) {
              if (r.message && r.message.status === 'success') {
                 console.log(`Comment logged successfully: ${r.message.log_entry_name}`);
                 $input.addClass('highlight-success');
                 setTimeout(() => { $input.removeClass('highlight-success'); }, 1000);
              } else {
                 console.error("Failed to log comment:", r);
                 frappe.show_alert({ message: __("Failed to log comment for {0}", [student]), indicator: 'red' });
                 $input.addClass('highlight-error');
                 setTimeout(() => { $input.removeClass('highlight-error'); }, 1500);
              }
            },
            error: function(r) {
                console.error("API Error logging comment:", r);
                frappe.show_alert({ message: __("API Error logging comment for {0}", [student]), indicator: 'red' });
                 $input.addClass('highlight-error');
                 setTimeout(() => { $input.removeClass('highlight-error'); }, 1500);
            }
        });
    });
    
    if (!$('#assessment-tool-styles').length) {
        $('<style id="assessment-tool-styles">')
            .html('.highlight-success { background-color: #d4edda !important; transition: background-color 0.5s ease; } .highlight-error { background-color: #f8d7da !important; transition: background-color 0.5s ease; }')
            .appendTo('head');
    }
  }
})
