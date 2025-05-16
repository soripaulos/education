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

    // Helper function to collect and save a single student's data
    function saveStudentData(frm, student_id, result_table_el) {
        let student_data = {
            student: student_id,
            assessment_details: {},
            total_score: 0,
            comment: ""
        };

        // Collect all scores for this student
        result_table_el.find(`input[data-student="${student_id}"].student-result-data`).each(function() {
            let criteria = $(this).data().criteria;
            let score_value = parseFloat($(this).val());
            if (isNaN(score_value)) score_value = 0;

            let max_score_attr = $(this).data().maxscore; // Ensure attribute is lowercase 'maxscore' if that's what template uses
            if (max_score_attr !== undefined) {
                let max_score = flt(max_score_attr);
                if (score_value < 0) score_value = 0;
                if (score_value > max_score) {
                    score_value = max_score;
                }
            }
            student_data.assessment_details[criteria] = score_value;
            student_data.total_score += score_value;
        });

        // Update total score display for this student
        result_table_el.find(`span[data-student="${student_id}"].total-score`).html(student_data.total_score.toFixed(2));

        // Collect comment for this student
        let comment_val = result_table_el.find(`input[data-student="${student_id}"].result-comment`).val();
        if (comment_val !== undefined) { // Check for undefined in case element not found or no value
            student_data.comment = comment_val;
        }

        // Call backend to save this student's data
        frappe.call({
            method: 'education.education.api.mark_assessment_result',
            args: {
                assessment_plan: frm.doc.assessment_plan,
                student_data_json: JSON.stringify(student_data)
            },
            freeze: true,
            freeze_message: __("Saving for {0}...", [student_data.student_name || student_id]),
            callback: function (r) {
                if (r.message && r.message.name) {
                    console.log("Saved data for student:", student_id, r.message);
                    let result_doc = r.message;
                    
                    // Update grades for each criterion
                    if (result_doc.details) {
                        result_doc.details.forEach(function(detail) {
                            let grade_cell = result_table_el.find(`[data-criteria='${detail.assessment_criteria}'][data-student='${student_id}'].student-result-grade`);
                            if(grade_cell.length > 0) {
                                grade_cell.html(detail.grade || 'F');
                            }
                        });
                    }
                    // Update total grade
                    result_table_el.find(`span[data-student="${student_id}"].total-score-grade`).html(result_doc.grade || 'F');
                    
                    // Update or show link to Assessment Result document
                    let link_span_selector = `span[data-student="${student_id}"].total-result-link`;
                    let link_span = result_table_el.find(link_span_selector);
                    if (link_span.length > 0) {
                        link_span.css('display', 'inline-block');
                        link_span.find('a').attr('href', `/app/assessment-result/${result_doc.name}`).text(result_doc.name);
                    }
                    // Ensure submit button is available
                    if (!frm.doc.show_submit) {
                        frm.doc.show_submit = true;
                        frm.events.submit_result(frm); 
                    }
                } else {
                     frappe.show_alert({ message: __("Could not save data for {0}.", [student_id]), indicator: 'orange' });
                }
            },
            error: function(err) {
                console.error("Error saving student data:", err);
                frappe.show_alert({ message: __("Error saving data: {0}", [(err.responseJSON ? err.responseJSON.message : err.message) || "Unknown error"]), indicator: 'red' });
            }
        });
    }

    // Handle SCORE changes
    result_table.on('change', 'input.student-result-data', function (e) {
      let $input = $(e.target);
      let student_id = $input.data().student;
      
      // Validate input value
      let max_score_attr = $input.data().maxscore; // Ensure attribute is lowercase
      let max_score = max_score_attr !== undefined ? flt(max_score_attr) : Infinity;
      let value = $input.val();
      let score = parseFloat(value);

      if (isNaN(score) || value === '') { score = 0; $input.val(0); }
      else if (score < 0) { score = 0; $input.val(0); }
      else if (score > max_score) { 
          score = max_score; 
          $input.val(max_score); 
          frappe.show_alert({ message: __("Score cannot exceed Maximum Score ({0})", [max_score]), indicator: 'orange' });
      }
      saveStudentData(frm, student_id, result_table);
    });
    
    // Handle COMMENT changes
    result_table.on('change', 'input.result-comment', function (e) {
      let $input = $(e.target);
      let student_id = $input.data().student;
      saveStudentData(frm, student_id, result_table);
    });
  },

  submit_result: function (frm) {
    if (frm.doc.show_submit) { // Check if submit should be enabled (e.g., after data is loaded)
      frm.page.set_primary_action(__('Submit All Results'), function () {
        let all_students_data = [];
        let result_table_el = $(frm.fields_dict.result_html.wrapper);
        let student_ids_processed = new Set(); // To handle each student once

        // Iterate over a known list of students or unique input fields to gather data
        // Assuming frm.doc.students contains the list of student IDs displayed
        if (frm.doc.students && frm.doc.students.length > 0) {
            frm.doc.students.forEach(function(student_meta) {
                let student_id = student_meta.student; // Assuming student_meta has a .student property for ID
                if (!student_id || student_ids_processed.has(student_id)) {
                    return; // Skip if no student_id or already processed
                }

                let student_data = {
                    student: student_id,
                    student_name: student_meta.student_name, // Include name for potential use in messages
                    assessment_details: {},
                    total_score: 0,
                    comment: ""
                };

                // Collect scores for this student
                result_table_el.find(`input[data-student="${student_id}"].student-result-data`).each(function() {
                    let criteria = $(this).data().criteria;
                    let score_value = parseFloat($(this).val());
                    if (isNaN(score_value)) score_value = 0;
                    
                    let max_score_attr = $(this).data().maxscore;
                    if (max_score_attr !== undefined) {
                        let max_score = flt(max_score_attr);
                        if (score_value < 0) score_value = 0;
                        if (score_value > max_score) {
                            score_value = max_score;
                        }
                    }
                    student_data.assessment_details[criteria] = score_value;
                    student_data.total_score += score_value;
                });

                // Collect comment for this student
                let comment_val = result_table_el.find(`input[data-student="${student_id}"].result-comment`).val();
                if (comment_val !== undefined) {
                    student_data.comment = comment_val;
                }
                all_students_data.push(student_data);
                student_ids_processed.add(student_id);
            });
        } else {
            frappe.show_alert({message: __("No student data to submit."), indicator: "orange"});
            return;
        }

        if (all_students_data.length === 0) {
            frappe.show_alert({message: __("No data collected to submit."), indicator: "orange"});
            return;
        }

        frappe.call({
          method: 'education.education.api.submit_assessment_results',
          args: {
            assessment_plan: frm.doc.assessment_plan,
            // student_group is still useful for context or if backend needs it for other logic
            student_group: frm.doc.student_group, 
            all_students_data_json: JSON.stringify(all_students_data)
          },
          freeze: true,
          freeze_message: __("Submitting all assessment results..."),
          callback: function (r) {
            if (r.message && r.message.status === "success") {
              frappe.msgprint(__('Assessment Results submitted successfully for {0} students.', [r.message.submitted_count]));
              frm.events.assessment_plan(frm); // Refresh the view
            } else if (r.message && r.message.status === "partial_success") {
              frappe.show_alert({
                message: __("Partially submitted: {0} succeeded, {1} failed. Check logs for details.", [r.message.submitted_count, r.message.failed_count]),
                indicator: "orange"
              });
              frm.events.assessment_plan(frm); // Refresh
            } else {
              frappe.show_alert({ message: __('Error submitting assessment results: {0}', [(r.message ? r.message.error : "Unknown error")]), indicator: 'red' });
            }
          },
          error: function(err) {
            console.error("Error submitting all results:", err);
            frappe.show_alert({ message: __("Error submitting results: {0}", [(err.responseJSON ? err.responseJSON.message : err.message) || "Unknown error"]), indicator: 'red' });
          }
        });
      });
    } else {
      // If show_submit is false, perhaps clear the primary action or set a default one
      frm.page.clear_primary_action();
    }
  }
}); 