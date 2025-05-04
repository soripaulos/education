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
      frm.trigger('assessment_plan')
    }
    frm.disable_save()
    frm.page.clear_indicator()
  },

  assessment_plan: function (frm) {
    frm.doc.show_submit = false
    if (frm.doc.assessment_plan) {
      if (!frm.doc.student_group) return
      frappe.call({
        method: 'education.education.api.get_assessment_students',
        args: {
          assessment_plan: frm.doc.assessment_plan,
          student_group: frm.doc.student_group,
        },
        callback: function (r) {
          if (r.message) {
            frm.doc.students = r.message
            frm.events.render_table(frm)
            for (let value of r.message) {
              if (!value.docstatus) {
                frm.doc.show_submit = true
                break
              }
            }
            frm.events.submit_result(frm)
          }
        },
      })
    }
  },

  render_table: function (frm) {
    $(frm.fields_dict.result_html.wrapper).empty()
    let assessment_plan = frm.doc.assessment_plan
    frappe.call({
      method: 'education.education.api.get_assessment_details',
      args: {
        assessment_plan: assessment_plan,
      },
      callback: function (r) {
        frm.events.get_marks(frm, r.message)
      },
    })
  },

  get_marks: function (frm, criteria_list) {
    let max_total_score = 0
    criteria_list.forEach(function (c, index) { // Added index for criteria
      c._index = index; // Store index in the criteria object
      max_total_score += c.maximum_score
    })
    var result_table = $(
      frappe.render_template('assessment_result_tool', {
        frm: frm,
        students: frm.doc.students,
        criteria: criteria_list,
        max_total_score: max_total_score,
      })
    )
    result_table.appendTo(frm.fields_dict.result_html.wrapper)

    $('.assessment-criteria').on('keydown', function (e) {
      // get data-criteria attribute
      let criteriaIndex = cint(
        e.target.parentElement.getAttribute('data-criteria-index')
      )
      changeFocusToNextCell(e, 2 + criteriaIndex)
    })

    $('.result-comment').on('keydown', function (e) {
      changeFocusToNextCell(e, 5)
    })

    function changeFocusToNextCell(e, cellIndex) {
      if (e.keyCode === 13 && !e.shiftKey) {
        let nextRow = e.target.parentElement.parentElement.nextElementSibling
        if (nextRow) {
          nextRow.cells[cellIndex].lastElementChild.focus()
        }
      }
      if (e.keyCode === 13 && e.shiftKey) {
        let prevRow =
          e.target.parentElement.parentElement.previousElementSibling
        if (prevRow) {
          prevRow.cells[cellIndex].lastElementChild.focus()
        }
      }
    }

    result_table.on('change', 'input', function (e) {
      let $input = $(e.target)
      let student = $input.data().student
      let max_score = $input.data().maxScore
      let value = $input.val()
      
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
      
      // Recalculate total score for the specific student
      let total_score = 0
      let student_scores = {}
      student_scores['assessment_details'] = {}
      let all_criteria_filled = true; // Flag to check if all inputs have values
      
      result_table
        .find(`input[data-student=${student}].student-result-data`)
        .each(function (el, input) {
          let $current_input = $(input);
          let criteria = $current_input.data().criteria;
          let criteria_value = parseFloat($current_input.val());
          
          if (!isNaN(criteria_value)) {
            student_scores['assessment_details'][criteria] = criteria_value;
            total_score += criteria_value; // Accumulate total score only for valid numbers
          } else {
            // Still add the key, but with 0, to ensure length check is accurate
            student_scores['assessment_details'][criteria] = 0;
            all_criteria_filled = false; // Mark as not all filled if any NaN is found
          }
        });
        
      // Update the total score display immediately
      result_table
        .find(`span[data-student=${student}].total-score`)
        .html(total_score);
        
      // Log the check for saving
      let criteria_count = Object.keys(student_scores['assessment_details']).length;
      console.log(`Checking save condition for student ${student}: Filled criteria = ${criteria_count}, Total criteria = ${criteria_list.length}, All filled flag = ${all_criteria_filled}`);

      // Check if all criteria have been filled (using the flag now)
      // if (all_criteria_filled && criteria_count === criteria_list.length) { // Original condition might be too strict
      // Let's try saving whenever *any* valid score is entered for now, 
      // but ensure all criteria keys exist in the payload (even if 0).
      if (criteria_count === criteria_list.length) { // Simplified check: ensure all keys are present
        student_scores['student'] = student
        student_scores['total_score'] = total_score
        result_table
          .find(`[data-student=${student}].result-comment`)
          .each(function (el, input) {
            student_scores['comment'] = $(input).val() || ""; // Ensure comment is always a string
          })
          
        console.log(`Attempting to save draft for student ${student} with scores:`, student_scores);
          
        frappe.call({
          method: 'education.education.api.mark_assessment_result',
          args: {
            assessment_plan: frm.doc.assessment_plan,
            scores: student_scores,
          },
          callback: function (r) {
            if (r.message) {
                let assessment_result = r.message
                console.log(`Draft saved successfully for student ${student}:`, assessment_result);
                if (!frm.doc.show_submit) {
                  frm.doc.show_submit = true
                  frm.events.submit_result(frm) // Call submit_result to potentially show the button
                }
                // Update grades and link after successful save
                for (var criteria_key of Object.keys(assessment_result.details)) {
                  result_table
                    .find(
                      `[data-criteria=${criteria_key}][data-student=${assessment_result.student}].student-result-grade`
                    )
                    .each(function (e1, input_el) {
                      $(input_el).html(assessment_result.details[criteria_key])
                    })
                }
                result_table
                  .find(
                    `span[data-student=${assessment_result.student}].total-score-grade`
                  )
                  .html(assessment_result.grade)
                let link_span = result_table.find(
                  `span[data-student=${assessment_result.student}].total-result-link`
                )
                $(link_span).css('display', 'block')
                $(link_span)
                  .find('a')
                  .attr('href', '/app/assessment-result/' + assessment_result.name)
            } else {
                console.error(`Failed to save draft for student ${student}. Response:`, r);
                frappe.show_alert({ message: __("Failed to save draft result for {0}", [student]), indicator: 'red' });
            }
          },
          error: function(r) {
             console.error(`API Error saving draft for student ${student}:`, r);
             frappe.show_alert({ message: __("API Error saving draft for {0}", [student]), indicator: 'red' });
          }
        })
      } else {
          console.log(`Save condition not met for student ${student}. Filled: ${criteria_count}/${criteria_list.length}`);
      }
    })
  },

  submit_result: function (frm) {
    if (frm.doc.show_submit) {
      frm.page.set_primary_action(__('Submit'), function () {
        frappe.call({
          method: 'education.education.api.submit_assessment_results',
          args: {
            assessment_plan: frm.doc.assessment_plan,
            student_group: frm.doc.student_group,
          },
          callback: function (r) {
            if (r.message) {
              frappe.msgprint(__('{0} Result submittted', [r.message]))
            } else {
              frappe.msgprint(__('No Result to submit'))
            }
            frm.events.assessment_plan(frm)
          },
        })
      })
    } else {
      frm.page.clear_primary_action()
    }
  },
})
