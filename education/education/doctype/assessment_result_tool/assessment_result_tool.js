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
    if (!assessment_plan) {
      frappe.show_alert({ message: __('Please select an Assessment Plan first.'), indicator: 'orange' });
      return;
    }
    if (!frm.doc.student_group) {
      frappe.show_alert({ message: __('Student Group not set. Please ensure it is fetched or set correctly.'), indicator: 'orange' });
      return;
    }
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
    criteria_list.forEach(function (c) {
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

    result_table.on('change', 'input.student-result-data, input.result-comment', function (e) {
      let $input = $(e.target);
      let student = $input.data().student;
      let isCommentField = $input.hasClass('result-comment');

      let $student_row_score_inputs = result_table.find(
        `input.student-result-data[data-student="${student}"]`
      );
      let $student_comment_input = result_table.find(
        `input.result-comment[data-student="${student}"]`
      );

      let student_scores = {
        student: student,
        assessment_details: {},
        total_score: 0,
        comment: $student_comment_input.val() || '',
        all_scores_valid: true,
      };

      let current_total_score = 0;
      let all_criteria_filled_and_valid = true;

      $student_row_score_inputs.each(function () {
        let $current_score_input = $(this);
        let criteria = $current_score_input.data().criteria;
        let max_score = parseFloat($current_score_input.data().maxScore);
        let value_str = $current_score_input.val();
        let value = parseFloat(value_str);

        if (value_str === '' || Number.isNaN(value)) {
          all_criteria_filled_and_valid = false;
        } else if (value < 0) {
          frappe.show_alert({ message: `Score for ${criteria} cannot be negative. Setting to 0.`, indicator: 'orange' });
          $current_score_input.val(0);
          value = 0;
        } else if (value > max_score) {
          frappe.show_alert({ message: `Score for ${criteria} cannot exceed ${max_score}. Setting to ${max_score}.`, indicator: 'orange' });
          $current_score_input.val(max_score);
          value = max_score;
        }

        if (!Number.isNaN(value)) {
          student_scores['assessment_details'][criteria] = value;
          current_total_score += value;
        } else {
           student_scores['assessment_details'][criteria] = null; 
           all_criteria_filled_and_valid = false; 
        }
      });
      
      student_scores['total_score'] = current_total_score;

      let $total_score_span = result_table.find(`span.total-score[data-student="${student}"]`);
      if (all_criteria_filled_and_valid) {
        $total_score_span.html(current_total_score);
      } else {
        $total_score_span.html('<span class="text-muted">' + __('Pending Input') + '</span>');
      }
      
      if (all_criteria_filled_and_valid || (isCommentField && Object.keys(student_scores['assessment_details']).length === criteria_list.length)) {
        criteria_list.forEach(c => {
          if(!(c.assessment_criteria in student_scores.assessment_details) || student_scores.assessment_details[c.assessment_criteria] === null) {
             if(!isCommentField && !all_criteria_filled_and_valid){
                console.warn("Trying to mark assessment with incomplete/invalid scores for student:", student);
             }
          }
        });

        frappe.call({
          method: 'education.education.api.mark_assessment_result',
          args: {
            assessment_plan: frm.doc.assessment_plan,
            scores: student_scores, 
          },
          callback: function (r) {
            if (r.message && r.message.name) {
              frappe.show_alert({ message: __(`Result for ${student} saved: ${r.message.name}`), indicator: 'green' });
              let assessment_result = r.message;
              if (!frm.doc.show_submit) {
                frm.doc.show_submit = true;
                frm.events.submit_result(frm); 
              }
              for (var criteria_key of Object.keys(assessment_result.details)) {
                result_table
                  .find(
                    `[data-criteria='${criteria_key}'][data-student='${assessment_result.student}'].student-result-grade`
                  )
                  .each(function (e1, input_grade_span) {
                    $(input_grade_span).html(assessment_result.details[criteria_key]);
                  });
              }
              result_table
                .find(
                  `span.total-score-grade[data-student='${assessment_result.student}']`
                )
                .html(assessment_result.grade);
              let link_span = result_table.find(
                `span.total-result-link[data-student='${assessment_result.student}']`
              );
              $(link_span).css('display', 'block');
              $(link_span)
                .find('a')
                .attr('href', '/app/assessment-result/' + assessment_result.name);
            } else {
              frappe.show_alert({ message: __(`Could not save result for ${student}. ${r.message || 'No details provided.'}`), indicator: 'red' });
              console.error("Failed to mark assessment result:", r);
            }
          },
          error: function(r) {
            frappe.show_alert({ message: __(`Error saving result for ${student}: ${r.statusText || 'Server error'}`), indicator: 'red' });
            console.error("API Error marking assessment result:", r);
          }
        });
      } else if (!isCommentField) {
      }
    });
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
